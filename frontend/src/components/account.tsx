import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Database } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { Link } from 'react-router'

import { ApiError, request } from '../api/client'
import { mutate, type Account } from '../api/learning'
import { card, Failure, field, PageHeading, Pending, primary, secondary } from './layout'

const accountKey = ['account']

export function useAccount() {
  return useQuery({
    queryKey: accountKey,
    queryFn: async () => {
      try {
        return await request<Account>('/me')
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) return null
        throw error
      }
    },
    retry: false,
  })
}

function Welcome() {
  const client = useQueryClient()
  const [register, setRegister] = useState(false)
  const mutation = useMutation({
    mutationFn: (form: { email: string; password: string }) => mutate<Account>(
      register ? '/auth/register' : '/auth/login', form,
    ),
    onSuccess: (account) => {
      client.removeQueries({ predicate: (query) => query.queryKey[0] !== 'account' })
      client.setQueryData(accountKey, account)
    },
  })

  return (
    <section className="mx-auto max-w-3xl">
      <div className="mb-6 inline-flex rounded-2xl bg-green-100 p-4 text-green-900"><Database size={28} aria-hidden="true" /></div>
      <PageHeading title="Adaptive DBMS Tutor">Practice DBMS and SQL with feedback and a personalized next step. Your account and learning data stay on this installation.</PageHeading>
      <div className={`${card} mt-8 max-w-md`}>
        <h2 className="text-xl font-semibold">{register ? 'Create a local account' : 'Sign in'}</h2>
        <form className="mt-4 grid gap-4" onSubmit={(event) => {
          event.preventDefault()
          const fields = new FormData(event.currentTarget)
          mutation.mutate({ email: String(fields.get('email')), password: String(fields.get('password')) })
        }}>
          <label className="grid gap-2 text-sm font-medium">Email
            <input className={field} name="email" type="email" autoComplete="username" required />
          </label>
          <label className="grid gap-2 text-sm font-medium">Password
            <input className={field} name="password" type="password" minLength={10} maxLength={128}
              autoComplete={register ? 'new-password' : 'current-password'} required />
          </label>
          {register && <p className="text-sm text-stone-600">Choose a password with at least 10 characters.</p>}
          <button className={primary} disabled={mutation.isPending}>{mutation.isPending ? 'Working…' : register ? 'Create account' : 'Sign in'}</button>
        </form>
        <Failure error={mutation.error} />
        <div className="mt-5 flex flex-wrap gap-3">
          <button className={secondary} type="button" onClick={() => { mutation.reset(); setRegister(!register) }}>
            {register ? 'Use an existing account' : 'Create an account'}
          </button>
          <Link className={secondary} to="/demo">Learner demo</Link>
        </div>
      </div>
    </section>
  )
}

export function RequireAccount({ children }: { children: (account: Account) => ReactNode }) {
  const me = useAccount()
  if (me.isPending) return <Pending>Checking your session…</Pending>
  if (me.isError) return <Failure error={me.error} retry={() => void me.refetch()} />
  if (!me.data) return <Welcome />
  return children(me.data)
}

export function useClearAccount() {
  const client = useQueryClient()
  return () => {
    client.setQueryData(accountKey, null)
    client.removeQueries({ predicate: (query) => query.queryKey[0] !== 'account' })
  }
}

export function useSetAccount() {
  const client = useQueryClient()
  return (account: Account) => client.setQueryData(accountKey, account)
}
