import { useEffect, useRef, useState } from 'react'
import { uploadPDF, getFiles } from '../api/client'
import type { UploadedFile } from '../types'

export default function FileUpload() {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [uploading, setUploading] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    getFiles().then(setFiles).catch(console.error)
  }, [])

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      await uploadPDF(file)
      const updated = await getFiles()
      setFiles(updated)
    } catch {
      alert('Upload failed')
    } finally {
      setUploading(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  return (
    <div className="p-4 flex-1 overflow-y-auto">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-gray-700 text-sm">Documents</h2>
        <button
          onClick={() => inputRef.current?.click()}
          disabled={uploading}
          className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {uploading ? 'Uploading...' : '+ PDF'}
        </button>
        <input ref={inputRef} type="file" accept=".pdf" className="hidden" onChange={handleUpload} />
      </div>
      {files.length === 0 ? (
        <p className="text-xs text-gray-400">No documents yet. Upload a PDF to start.</p>
      ) : (
        <ul className="space-y-2">
          {files.map(f => (
            <li key={f.id} className="text-xs text-gray-600 bg-gray-50 rounded-lg p-2">
              <div className="flex items-center gap-1">
                <span>📄</span>
                <span className="truncate font-medium">{f.filename}</span>
              </div>
              <div className="text-gray-400 mt-1">{f.chunk_count} chunks</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
