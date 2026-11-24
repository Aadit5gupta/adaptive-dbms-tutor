export type SourceKind = 'book' | 'lesson'

export interface Citation {
  id: string
  kind: SourceKind
  title: string
  url: string
  attribution: string
  license_url: string | null
  lesson_ref: string | null
}

export interface Book {
  id: string
  title: string
  authors: string[]
  source_url: string
  license: string | null
  license_evidence_url: string
  indexed_sections: number
  cleared_sections: number
  section_exceptions: { section_url: string; issue: string; status: string }[]
}

export interface Library {
  catalog_books: number
  indexed_books: number
  books: Book[]
}

export interface SearchHit {
  citation: Citation
  topic_id: string
  excerpt: string
}
