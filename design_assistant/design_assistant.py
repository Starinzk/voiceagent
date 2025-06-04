import logging
import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import cartesia, deepgram, openai, silero
from livekit.plugins import noise_cancellation

from design_utils import load_prompt
from design_database import CustomerDatabase

logger = logging.getLogger("personal-shopper")
logger.setLevel(logging.INFO)

load_dotenv()

# Initialize the customer database
db = CustomerDatabase()

@dataclass
class UserData:
    """Class to store user data and agents during a call.
    
    Attributes:
        personas (dict[str, Agent]): Dictionary mapping agent names to their instances
        prev_agent (Optional[Agent]): The previous agent that handled the call
        ctx (Optional[JobContext]): The current job context
        first_name (Optional[str]): Customer's first name
        last_name (Optional[str]): Customer's last name
        customer_id (Optional[str]): Customer's unique identifier
        current_order (Optional[dict]): Current order being processed
        status (str): The current status of the customer's workflow
    """
    personas: dict[str, Agent] = field(default_factory=dict)
    prev_agent: Optional[Agent] = None
    ctx: Optional[JobContext] = None

    # Customer information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    customer_id: Optional[str] = None
    current_order: Optional[dict] = None
    status: str = "awaiting_intent"

    def is_identified(self) -> bool:
        """Check if the customer is identified.
        
        Returns:
            bool: True if both first_name and last_name are set, False otherwise
        """
        return self.first_name is not None and self.last_name is not None

    def reset(self) -> None:
        """Reset all customer information to None.
        
        This method clears the customer's name, ID, and current order information.
        """
        self.first_name = None
        self.last_name = None
        self.customer_id = None
        self.current_order = None

    def summarize(self) -> str:
        """Return a summary of the user data.
        
        Returns:
            str: A formatted string containing customer information if identified,
                or "Customer not yet identified" if not identified.
        """
        if self.is_identified():
            return f"Customer: {self.first_name} {self.last_name} (ID: {self.customer_id})"
        return "Customer not yet identified."

RunContext_T = RunContext[UserData]

class BaseAgent(Agent):
    async def on_enter(self) -> None:
        """Initialize the agent when entering a new session.
        
        This method:
        1. Sets the agent's name in the room attributes
        2. Creates a personalized prompt based on customer identification
        3. Copies context from the previous agent if it exists
        4. Updates the chat context with system message
        5. Triggers the first response generation
        """
        agent_name = self.__class__.__name__
        logger.info(f"Entering {agent_name}")

        userdata: UserData = self.session.userdata
        if userdata.ctx and userdata.ctx.room:
            await userdata.ctx.room.local_participant.set_attributes({"agent": agent_name})

        # Create a personalized prompt based on customer identification
        custom_instructions = self.instructions
        if userdata.is_identified():
            custom_instructions += f"\n\nYou are speaking with {userdata.first_name} {userdata.last_name}."

        chat_ctx = self.chat_ctx.copy()

        # Copy context from previous agent if it exists
        if userdata.prev_agent:
            items_copy = self._truncate_chat_ctx(
                userdata.prev_agent.chat_ctx.items, keep_function_call=True
            )
            existing_ids = {item.id for item in chat_ctx.items}
            items_copy = [item for item in items_copy if item.id not in existing_ids]
            chat_ctx.items.extend(items_copy)

        chat_ctx.add_message(
            role="system",
            content=f"You are the {agent_name}. {userdata.summarize()}"
        )
        await self.update_chat_ctx(chat_ctx)
        self.session.generate_reply()

    def _truncate_chat_ctx(
        self,
        items: list,
        keep_last_n_messages: int = 6,
        keep_system_message: bool = False,
        keep_function_call: bool = False,
    ) -> list:
        """Truncate the chat context to keep the last n messages.
        
        Args:
            items (list): List of chat context items to truncate
            keep_last_n_messages (int, optional): Number of messages to keep. Defaults to 6.
            keep_system_message (bool, optional): Whether to keep system messages. Defaults to False.
            keep_function_call (bool, optional): Whether to keep function calls. Defaults to False.
            
        Returns:
            list: Truncated list of chat context items
            
        Note:
            Items are processed in reverse order, keeping the most recent messages
            that match the specified criteria.
        """
        def _valid_item(item) -> bool:
            if not keep_system_message and item.type == "message" and item.role == "system":
                return False
            if not keep_function_call and item.type in ["function_call", "function_call_output"]:
                return False
            return True

        new_items = []
        for item in reversed(items):
            if _valid_item(item):
                new_items.append(item)
            if len(new_items) >= keep_last_n_messages:
                break
        new_items = new_items[::-1]

        while new_items and new_items[0].type in ["function_call", "function_call_output"]:
            new_items.pop(0)

        return new_items

    async def _transfer_to_agent(self, name: str, context: RunContext_T) -> Agent:
        """Transfer to another agent while preserving context.
        
        Args:
            name (str): Name of the agent to transfer to
            context (RunContext_T): Current run context
            
        Returns:
            Agent: The next agent to handle the session
            
        Note:
            This method preserves the chat context and updates the previous agent reference.
        """
        userdata = context.userdata
        current_agent = context.session.current_agent
        next_agent = userdata.personas[name]
        userdata.prev_agent = current_agent

        return next_agent


class TriageAgent(BaseAgent):
    def __init__(self) -> None:
        """Initialize the Triage agent with specific configuration.
        
        Sets up the agent with:
        - Triage-specific instructions from YAML
        - Deepgram for speech-to-text
        - OpenAI GPT-4 for language model
        - Cartesia for text-to-speech
        - Silero for voice activity detection
        """
        super().__init__(
            instructions=load_prompt('triage_prompt.yaml'),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load()
        )

    @function_tool
    async def identify_customer(self, first_name: str, last_name: str):
        """Identify a customer by their first and last name.
        
        Args:
            first_name (str): The customer's first name
            last_name (str): The customer's last name
            
        Returns:
            str: Confirmation message with the customer's first name
        """
        userdata: UserData = self.session.userdata
        userdata.first_name = first_name
        userdata.last_name = last_name
        userdata.customer_id = db.get_or_create_customer(first_name, last_name)

        return f"Thank you, {first_name}. I've found your account."

    @function_tool
    async def transfer_to_sales(self, context: RunContext_T) -> Agent:
        """Transfer the customer to the Sales agent.
        
        Args:
            context (RunContext_T): Current run context
            
        Returns:
            Agent: The Sales agent instance
            
        Note:
            Provides a personalized message if the customer is identified.
        """
        # Create a personalized message if customer is identified
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you to our Sales team who can help you find the perfect product."
        else:
            message = "I'll transfer you to our Sales team who can help you find the perfect product."

        await self.session.say(message)
        return await self._transfer_to_agent("sales", context)

    @function_tool
    async def transfer_to_returns(self, context: RunContext_T) -> Agent:
        """Transfer the customer to the Returns agent.
        
        Args:
            context (RunContext_T): Current run context
            
        Returns:
            Agent: The Returns agent instance
            
        Note:
            Provides a personalized message if the customer is identified.
        """
        # Create a personalized message if customer is identified
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you to our Returns department who can assist with your return or exchange."
        else:
            message = "I'll transfer you to our Returns department who can assist with your return or exchange."

        await self.session.say(message)
        return await self._transfer_to_agent("returns", context)


class DesignCoachAgent(BaseAgent):
    def __init__(self) -> None:
        """Initialize the Design Coach agent with specific configuration.
        
        Sets up the agent with:
        - Design Coach-specific instructions from YAML
        - Deepgram for speech-to-text
        - OpenAI GPT-4 for language model
        - Cartesia for text-to-speech
        - Silero for voice activity detection
        """
        super().__init__(
            instructions=load_prompt('design_coach.yaml'),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load()
        )

    async def on_enter(self) -> None:
        """Set initial status when agent enters."""
        self.session.userdata.status = "awaiting_problem_definition"
        await super().on_enter()

    @function_tool
    async def identify_customer(self, first_name: str, last_name: str):
        """Identify a customer by their first and last name.
        
        Args:
            first_name (str): The customer's first name
            last_name (str): The customer's last name
            
        Returns:
            str: Confirmation message with the customer's first name
        """
        userdata: UserData = self.session.userdata
        userdata.first_name = first_name
        userdata.last_name = last_name
        userdata.customer_id = db.get_or_create_customer(first_name, last_name)

        return f"Thank you, {first_name}. I've found your account."

    @function_tool
    async def start_order(self):
        """Start a new order for the customer.
        
        Returns:
            str: Confirmation message or error if customer not identified
            
        Note:
            Initializes an empty items list in the current order.
        """
        userdata: UserData = self.session.userdata
        if not userdata.is_identified():
            return "Please identify the customer first using the identify_customer function."

        userdata.current_order = {
            "items": []
        }

        return "I've started a new order for you. What would you like to purchase?"

    @function_tool
    async def add_item_to_order(self, item_name: str, quantity: int, price: float):
        """Add an item to the current order.
        
        Args:
            item_name (str): The name of the item
            quantity (int): The quantity to purchase
            price (float): The price per item
            
        Returns:
            str: Confirmation message or error if customer not identified
        """
        userdata: UserData = self.session.userdata
        if not userdata.is_identified():
            return "Please identify the customer first using the identify_customer function."

        if not userdata.current_order:
            userdata.current_order = {"items": []}

        item = {
            "name": item_name,
            "quantity": quantity,
            "price": price
        }

        userdata.current_order["items"].append(item)

        return f"Added {quantity}x {item_name} to your order."

    @function_tool
    async def complete_order(self):
        """Complete the current order and save it to the database.
        
        Returns:
            str: Order summary including order ID, total, and itemized list,
                or error message if no items in order or customer not identified
                
        Note:
            Calculates order total and saves the order to the database.
            Resets the current order after completion.
        """
        userdata: UserData = self.session.userdata
        if not userdata.is_identified():
            return "Please identify the customer first using the identify_customer function."

        if not userdata.current_order or not userdata.current_order.get("items"):
            return "There are no items in the current order."

        # Calculate order total
        total = sum(item["price"] * item["quantity"] for item in userdata.current_order["items"])
        userdata.current_order["total"] = total

        # Save order to database
        order_id = db.add_order(userdata.customer_id, userdata.current_order)

        # Create a summary of the order
        summary = f"Order #{order_id} has been completed. Total: ${total:.2f}\n"
        summary += "Items:\n"
        for item in userdata.current_order["items"]:
            summary += f"- {item['quantity']}x {item['name']} (${item['price']} each)\n"

        # Reset the current order
        userdata.current_order = None

        return summary

    @function_tool
    async def transfer_to_triage(self, context: RunContext_T) -> Agent:
        # Create a personalized message if customer is identified
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you back to our Triage agent who can better direct your inquiry."
        else:
            message = "I'll transfer you back to our Triage agent who can better direct your inquiry."

        await self.session.say(message)
        return await self._transfer_to_agent("triage", context)

    @function_tool
    async def transfer_to_returns(self, context: RunContext_T) -> Agent:
        # Create a personalized message if customer is identified
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you to our Returns department for assistance with your return request."
        else:
            message = "I'll transfer you to our Returns department for assistance with your return request."

        await self.session.say(message)
        return await self._transfer_to_agent("returns", context)


class DesignStrategistAgent(BaseAgent):
    def __init__(self) -> None:
        """Initialize the Design Strategist agent with specific configuration.
        
        Sets up the agent with:
        - Design Strategist-specific instructions from YAML
        - Deepgram for speech-to-text
        - OpenAI GPT-4 for language model
        - Cartesia for text-to-speech
        - Silero for voice activity detection
        """
        super().__init__(
            instructions=load_prompt('design_strategist.yaml'),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load()
        )

    async def on_enter(self) -> None:
        """Set initial status when agent enters."""
        self.session.userdata.status = "ready_for_evaluation"
        await super().on_enter()

    @function_tool
    async def identify_customer(self, first_name: str, last_name: str):
        """Identify a customer by their first and last name.
        
        Args:
            first_name (str): The customer's first name
            last_name (str): The customer's last name
            
        Returns:
            str: Confirmation message with the customer's first name
        """
        userdata: UserData = self.session.userdata
        userdata.first_name = first_name
        userdata.last_name = last_name
        userdata.customer_id = db.get_or_create_customer(first_name, last_name)

        return f"Thank you, {first_name}. I've found your account."

    @function_tool
    async def transfer_to_triage(self, context: RunContext_T) -> Agent:
        # Create a personalized message if customer is identified
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you back to our Triage agent who can better direct your inquiry."
        else:
            message = "I'll transfer you back to our Triage agent who can better direct your inquiry."

        await self.session.say(message)
        return await self._transfer_to_agent("triage", context)

    @function_tool
    async def transfer_to_design_coach(self, context: RunContext_T) -> Agent:
        # Create a personalized message if customer is identified
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you to our Design Coach who can help you refine your design."
        else:
            message = "I'll transfer you to our Design Coach who can help you refine your design."

        await self.session.say(message)
        return await self._transfer_to_agent("design_coach", context)

    @function_tool
    async def transfer_to_design_strategist(self, context: RunContext_T) -> Agent:
        """Transfer the user to the Design Strategist agent."""
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you to our Design Strategist who can help you clarify your design problem."
        else:
            message = "I'll transfer you to our Design Strategist who can help you clarify your design problem."
        await self.session.say(message)
        return await self._transfer_to_agent("design_strategist", context)

    @function_tool
    async def transfer_to_design_evaluator(self, context: RunContext_T) -> Agent:
        """Transfer the user to the Design Evaluator agent."""
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you to our Design Evaluator for structured feedback."
        else:
            message = "I'll transfer you to our Design Evaluator for structured feedback."
        await self.session.say(message)
        return await self._transfer_to_agent("design_evaluator", context)

    @function_tool
    async def transfer_to_design_coach(self, context: RunContext_T) -> Agent:
        """Transfer the user back to the Design Coach agent."""
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you back to our Design Coach who can help you further clarify your intent."
        else:
            message = "I'll transfer you back to our Design Coach who can help you further clarify your intent."
        await self.session.say(message)
        return await self._transfer_to_agent("design_coach", context)


class DesignEvaluatorAgent(BaseAgent):
    def __init__(self) -> None:
        """Initialize the Design Evaluator agent with specific configuration.
        
        Sets up the agent with:
        - Design Evaluator-specific instructions from YAML
        - Deepgram for speech-to-text
        - OpenAI GPT-4 for language model
        - Cartesia for text-to-speech
        - Silero for voice activity detection
        """
        super().__init__(
            instructions=load_prompt('design_evaluator.yaml'),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load()
        )

    async def on_enter(self) -> None:
        """Set initial status when agent enters."""
        self.session.userdata.status = "evaluation_complete"
        await super().on_enter()

    @function_tool
    async def identify_customer(self, first_name: str, last_name: str):
        """Identify a customer by their first and last name.
        
        Args:
            first_name (str): The customer's first name
            last_name (str): The customer's last name
            
        Returns:
            str: Confirmation message with the customer's first name
        """
        userdata: UserData = self.session.userdata
        userdata.first_name = first_name
        userdata.last_name = last_name
        userdata.customer_id = db.get_or_create_customer(first_name, last_name)

        return f"Thank you, {first_name}. I've found your account."

    @function_tool
    async def get_order_history(self):
        """Get the order history for the current customer.
        
        Returns:
            str: Formatted order history or error if customer not identified
        """
        userdata: UserData = self.session.userdata
        if not userdata.is_identified():
            return "Please identify the customer first using the identify_customer function."

        order_history = db.get_customer_order_history(userdata.first_name, userdata.last_name)
        return order_history

    @function_tool
    async def process_return(self, order_id: int, item_name: str, reason: str):
        """Process a return for an item from a specific order.
        
        Args:
            order_id (int): The ID of the order containing the item to return
            item_name (str): The name of the item to return
            reason (str): The reason for the return
            
        Returns:
            str: Confirmation message with return details or error if customer not identified
            
        Note:
            In a real system, this would update the order in the database.
            Currently returns a confirmation message with refund timeline.
        """
        userdata: UserData = self.session.userdata
        if not userdata.is_identified():
            return "Please identify the customer first using the identify_customer function."

        # In a real system, we would update the order in the database
        # For this example, we'll just return a confirmation message
        return f"Return processed for {item_name} from Order #{order_id}. Reason: {reason}. A refund will be issued within 3-5 business days."

    @function_tool
    async def transfer_to_triage(self, context: RunContext_T) -> Agent:
        # Create a personalized message if customer is identified
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you back to our Triage agent who can better direct your inquiry."
        else:
            message = "I'll transfer you back to our Triage agent who can better direct your inquiry."

        await self.session.say(message)
        return await self._transfer_to_agent("triage", context)

    @function_tool
    async def transfer_to_design_strategist(self, context: RunContext_T) -> Agent:
        # Create a personalized message if customer is identified
        userdata: UserData = self.session.userdata
        if userdata.is_identified():
            message = f"Thank you, {userdata.first_name}. I'll transfer you to our Design Strategist who can help you refine your design."
        else:
            message = "I'll transfer you to our Design Strategist who can help you refine your design."

        await self.session.say(message)
        return await self._transfer_to_agent("design_strategist", context)


async def entrypoint(ctx: JobContext):
    """Initialize and start the personal shopper application.
    
    Args:
        ctx (JobContext): The job context containing room and connection information
        
    This function:
    1. Connects to the LiveKit server
    2. Initializes user data
    3. Creates agent instances (Triage, Design Coach, Design Strategist, Design Evaluator)
    4. Registers agents in userdata
    5. Creates and starts a session with the Triage agent
    """
    await ctx.connect()

    # Initialize user data with context
    userdata = UserData(ctx=ctx)

    # Create agent instances
    triage_agent = TriageAgent()
    design_coach_agent = DesignCoachAgent()
    design_strategist_agent = DesignStrategistAgent()
    design_evaluator_agent = DesignEvaluatorAgent()

    # Register all agents in the userdata
    userdata.personas.update({
        "triage": triage_agent,
        "design_coach": design_coach_agent,
        "design_strategist": design_strategist_agent,
        "design_evaluator": design_evaluator_agent
    })

    # Create session with userdata
    session = AgentSession[UserData](userdata=userdata)

    await session.start(
        agent=triage_agent,  # Start with the Triage agent
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
