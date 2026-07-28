import React, { useState } from 'react';

export default function GuardrailPanel(): React.ReactElement {
  const [coldStartPasses, setColdStartPasses] = useState(true);
  const candidate = coldStartPasses ? 0.305 : 0.271;
  const verdict = coldStartPasses ? 'MET in the synthetic fixture' : 'NOT MET: guardrail veto';
  return <div className="learning-widget">
    <label><input type="checkbox" checked={coldStartPasses} onChange={() => setColdStartPasses((value) => !value)} /> cold-start guardrail passes</label>
    <p>Headline nDCG@10 is a synthetic +0.1090 over popularity and +0.0550 over item-item CF. Cold-start candidate: <strong>{candidate.toFixed(3)}</strong>; baseline: 0.298.</p>
    <p><strong>{verdict}</strong>. Flip the guardrail: the same headline win becomes a mission failure. These are bundled illustrative fixtures, not mission results.</p>
  </div>;
}
