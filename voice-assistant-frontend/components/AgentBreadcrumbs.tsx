"use client";

const AGENTS = ["DesignCoachAgent", "DesignStrategistAgent", "DesignEvaluatorAgent"];

function formatAgentName(name: string): string {
  return name.replace(/Agent$/, "").replace(/([A-Z])/g, " $1").trim();
}

export function AgentBreadcrumbs({ currentAgentName }: { currentAgentName: string }) {
  const currentIndex = AGENTS.indexOf(currentAgentName);

  return (
    <div className="flex items-center justify-center space-x-2 text-sm text-enso-text/60 font-sans p-4">
      {AGENTS.map((agent, index) => (
        <div key={agent} className="flex items-center">
          <span
            className={`transition-all duration-300 ${
              index <= currentIndex ? "font-bold text-enso-text" : ""
            }`}
          >
            {formatAgentName(agent)}
          </span>
          {index < AGENTS.length - 1 && (
            <span
              className={`mx-2 transition-opacity duration-300 ${
                index < currentIndex ? "opacity-100" : "opacity-50"
              }`}
            >
              →
            </span>
          )}
        </div>
      ))}
    </div>
  );
} 