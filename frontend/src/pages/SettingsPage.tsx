import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'

import { mutate, type Account, type Goal, type Level } from '../api/learning'
import { useClearAccount, useSetAccount } from '../components/account'
import { card, Failure, field, PageHeading, primary, secondary, textLink } from '../components/layout'

export function SettingsPage({ account }: { account: Account }) {
  const clear = useClearAccount()
  const setAccount = useSetAccount()
  const [deleting, setDeleting] = useState(false)
  const save = useMutation({
    mutationFn: (values: FormData) => mutate<Account>('/me', {
      goal: (values.get('goal') as Goal) || null,
      level: (values.get('level') as Level) || null,
      daily_minutes: values.get('minutes') ? Number(values.get('minutes')) : null,
    }, { method: 'PATCH' }),
    onSuccess: setAccount,
  })
  const exit = useMutation({
    mutationFn: (remove: boolean) => remove ? mutate('/me', undefined, { method: 'DELETE' }) : mutate('/auth/logout'),
    onSuccess: clear,
  })

  return <>
    <PageHeading title="Settings">{account.email}</PageHeading>
    <div className="mt-7 grid gap-4 lg:grid-cols-2">
      <section className={card}>
        <h2 className="text-lg font-semibold">Learning preferences</h2>
        <form className="mt-4 grid gap-4" onSubmit={(event) => {
          event.preventDefault()
          save.mutate(new FormData(event.currentTarget))
        }}>
          <label className="grid gap-2 text-sm font-medium">Goal
            <select name="goal" className={field} defaultValue={account.preferences.goal ?? ''}>
              <option value="">Choose a goal</option><option value="exam">Prepare for an exam</option>
              <option value="placements">Prepare for placements</option><option value="understanding">Understand DBMS</option>
            </select>
          </label>
          <label className="grid gap-2 text-sm font-medium">Experience
            <select name="level" className={field} defaultValue={account.preferences.level ?? ''}>
              <option value="">Choose a level</option><option value="beginner">Beginner</option>
              <option value="some_experience">Some experience</option><option value="advanced">Advanced</option>
            </select>
          </label>
          <label className="grid gap-2 text-sm font-medium">Daily study minutes
            <input name="minutes" type="number" className={field} min={5} max={180}
              defaultValue={account.preferences.daily_minutes ?? ''} />
          </label>
          <button className={primary} disabled={save.isPending}>Save preferences</button>
          {save.isSuccess && <p className="text-sm text-green-900" role="status">Preferences saved.</p>}
          <Failure error={save.error} />
        </form>
      </section>
      <section className={card}>
        <h2 className="text-lg font-semibold">Account data</h2>
        <p className="mt-2 text-sm leading-6 text-stone-600">Export your profile, attempts and progress or remove all data for this account.</p>
        <div className="mt-4 grid justify-items-start gap-3">
          <a href="/api/v1/me/export" className={textLink}>Download my data</a>
          <button className={secondary} disabled={exit.isPending} onClick={() => exit.mutate(false)}>Sign out</button>
          <button className="text-sm font-semibold text-red-900 underline" onClick={() => setDeleting(!deleting)}>
            {deleting ? 'Cancel deletion' : 'Delete my account'}
          </button>
          {deleting && <div className="rounded-lg border border-red-200 bg-red-50 p-3">
            <p className="mb-3 text-sm text-red-900">This permanently removes your account and learning history.</p>
            <button disabled={exit.isPending} className="rounded-lg bg-red-900 px-3 py-2 text-sm font-semibold text-white"
              onClick={() => exit.mutate(true)}>Permanently delete account</button>
          </div>}
        </div>
        <Failure error={exit.error} />
      </section>
    </div>
  </>
}
