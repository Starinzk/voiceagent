"use client";

import React from 'react';

export interface ClarityCapsule {
  problem_statement: string;
  solution_concept: string;
  strengths: string[];
  blind_spots: string[];
  next_steps: string[];
}

interface ClarityCapsuleViewProps {
  capsule: ClarityCapsule;
}

export function ClarityCapsuleView({ capsule }: ClarityCapsuleViewProps) {
  const generateMarkdown = () => {
    return `
# Clarity Capsule

## Problem Statement
"${capsule.problem_statement}"

## Solution Concept
${capsule.solution_concept}

## Strengths
${capsule.strengths.map(s => `- ${s}`).join('\\n')}

## Blind Spots
${capsule.blind_spots.map(s => `- ${s}`).join('\\n')}

## Next Steps
${capsule.next_steps.map((s, i) => `${i + 1}. ${s}`).join('\\n')}
    `.trim();
  };

  const handleCopy = () => {
    const markdown = generateMarkdown();
    navigator.clipboard.writeText(markdown);
    alert("Copied to clipboard!");
  };

  const handleDownload = () => {
    const markdown = generateMarkdown();
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'clarity-capsule.md';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white/90 text-enso-text p-8 rounded-2xl shadow-2xl max-w-2xl mx-auto font-sans animate-fade-in-up">
      <h1 className="text-4xl font-serif text-center mb-6">Your Clarity Capsule</h1>
      
      <section className="mb-6">
        <h2 className="text-2xl font-serif mb-3 text-enso-text/80">Problem Statement</h2>
        <p className="text-lg bg-gray-100 p-4 rounded-lg">&ldquo;{capsule.problem_statement}&rdquo;</p>
      </section>

      <section className="mb-6">
        <h2 className="text-2xl font-serif mb-3 text-enso-text/80">Solution Concept</h2>
        <p className="text-lg">{capsule.solution_concept}</p>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <section>
          <h2 className="text-2xl font-serif mb-3 text-enso-text/80">Strengths</h2>
          <ul className="list-disc list-inside space-y-2">
            {capsule.strengths.map((item, index) => <li key={index} className="text-lg">{item}</li>)}
          </ul>
        </section>
        <section>
          <h2 className="text-2xl font-serif mb-3 text-enso-text/80">Blind Spots</h2>
          <ul className="list-disc list-inside space-y-2">
            {capsule.blind_spots.map((item, index) => <li key={index} className="text-lg">{item}</li>)}
          </ul>
        </section>
      </div>

      <section className="mb-8">
        <h2 className="text-2xl font-serif mb-3 text-enso-text/80">Next Steps</h2>
        <ul className="list-decimal list-inside space-y-2">
          {capsule.next_steps.map((item, index) => <li key={index} className="text-lg">{item}</li>)}
        </ul>
      </section>

      <div className="flex justify-center space-x-4">
        <button 
          onClick={handleCopy}
          className="px-6 py-2 bg-enso-card text-enso-text font-semibold rounded-full border border-enso-text/10 shadow-md hover:bg-enso-gradient hover:text-white transition-all duration-300"
        >
          📋 Copy as Markdown
        </button>
        <button 
          onClick={handleDownload}
          className="px-6 py-2 bg-enso-card text-enso-text font-semibold rounded-full border border-enso-text/10 shadow-md hover:bg-enso-gradient hover:text-white transition-all duration-300"
        >
          💾 Download .md
        </button>
      </div>
    </div>
  );
} 