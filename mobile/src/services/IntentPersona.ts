export type Persona = 'calm' | 'bold';

export function inferPersona(scores: { anxiety?: number; opportunity?: number }): Persona {
  const anxiety = Number(scores.anxiety ?? 0);
  const opportunity = Number(scores.opportunity ?? 0);
  if (anxiety > 0.6 && opportunity < 0.4) return 'calm';
  if (opportunity > 0.6) return 'bold';
  return 'calm';
}

export function personaCopy(persona: Persona) {
  return persona === 'bold'
    ? { title: 'Seize the opening', subtitle: 'Here are high-conviction ideas to consider' }
    : { title: 'Stay centered', subtitle: 'Here are steady moves aligned to your plan' };
}


