import type { Hypothesis } from '../api/learning'

const labels: Record<Hypothesis['state'], string> = {
  possible: 'Possible misconception',
  active: 'Active misconception',
  improving: 'Misconception improving',
  resolved: 'Misconception resolved',
}

export function MisconceptionStatus({ hypothesis }: { hypothesis: Hypothesis }) {
  const count = hypothesis.evidence_count
  return <div className="text-sm">
    <p className="font-semibold">{labels[hypothesis.state]}</p>
    <p className="mt-1 text-stone-700">{hypothesis.title}</p>
    <p className="mt-1 text-stone-600">{count} independent {count === 1 ? 'signal' : 'signals'}</p>
  </div>
}
