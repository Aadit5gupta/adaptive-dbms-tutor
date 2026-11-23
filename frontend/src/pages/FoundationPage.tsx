interface FoundationPageProps {
  title: string
  description: string
}

export function FoundationPage({ title, description }: FoundationPageProps) {
  return (
    <>
      <h1>{title}</h1>
      <p className="mt-4 max-w-xl text-lg leading-8 text-stone-600">{description}</p>
      <section className="mt-8 max-w-xl rounded-2xl border border-stone-200 bg-white p-7">
        <h2 className="text-lg font-semibold">Not available yet</h2>
        <p className="mt-2 leading-7 text-stone-600">
          Learning features will appear as they are implemented and the content is reviewed.
        </p>
      </section>
    </>
  )
}
