import React from 'react';
import { Sparkles, ArrowRight, CheckCircle2, PlayCircle, Eye, ShieldAlert } from 'lucide-react';

export default function HowToUseGuide({ onSelectScenario1, onSelectScenario2 }) {
  return (
    <div className="bg-gradient-to-r from-slate-900 via-purple-950/30 to-slate-900 border border-purple-500/30 rounded-2xl p-5 shadow-xl shadow-purple-950/20" data-testid="how-to-use-guide">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-purple-500/20 text-purple-300 border border-purple-500/30 flex items-center justify-center font-bold text-sm">
            💡
          </div>
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              How to Use SmartSub
              <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/40 font-semibold">
                3 Simple Steps
              </span>
            </h2>
            <p className="text-xs text-slate-300">
              New to fantasy cricket substitutions? Follow these three simple steps to see SmartSub in action.
            </p>
          </div>
        </div>

        <div className="text-xs text-slate-400 font-mono hidden lg:block">
          Average time to test: <strong className="text-purple-300">10 seconds</strong>
        </div>
      </div>

      {/* 3 Step Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
        {/* Step 1 */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between hover:border-purple-500/40 transition-all">
          <div>
            <div className="flex items-center gap-2 text-xs font-bold text-purple-400 uppercase tracking-wider font-mono mb-1.5">
              <span className="w-5 h-5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/40 flex items-center justify-center text-[11px]">
                1
              </span>
              Step 1: Select a Scenario
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Pick <strong className="text-white">Scenario 1</strong> (starter doesn't play) or <strong className="text-white">Scenario 2</strong> (mid-match Impact Player substitution).
            </p>
          </div>
        </div>

        {/* Step 2 */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between hover:border-purple-500/40 transition-all">
          <div>
            <div className="flex items-center gap-2 text-xs font-bold text-purple-400 uppercase tracking-wider font-mono mb-1.5">
              <span className="w-5 h-5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/40 flex items-center justify-center text-[11px]">
                2
              </span>
              Step 2: Run the Simulation
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Click the <strong className="text-white">"Start Scenario"</strong> button below or use the simulation controls to watch the pitch formation update automatically.
            </p>
          </div>
        </div>

        {/* Step 3 */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between hover:border-purple-500/40 transition-all">
          <div>
            <div className="flex items-center gap-2 text-xs font-bold text-purple-400 uppercase tracking-wider font-mono mb-1.5">
              <span className="w-5 h-5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/40 flex items-center justify-center text-[11px]">
                3
              </span>
              Step 3: View Decision & Points
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Read the AI tactical explanation and verify how points were secured and locked in the split innings ledger.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
