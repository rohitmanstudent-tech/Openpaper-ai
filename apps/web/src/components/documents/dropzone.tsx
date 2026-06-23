"use client"

import { useState, useCallback, useRef } from "react"
import { Upload, File, X, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface DropZoneProps {
  onUpload: (file: File) => Promise<void>
  accept?: string
  maxSize?: number
}

export function DropZone({ onUpload, accept = ".pdf,.docx,.xlsx,.txt,.md,.csv,.json", maxSize = 10 * 1024 * 1024 }: DropZoneProps) {
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = useCallback(async (f: File) => {
    if (f.size > maxSize) return
    setFile(f)
    setUploading(true)
    try {
      await onUpload(f)
    } finally {
      setUploading(false)
      setFile(null)
    }
  }, [onUpload, maxSize])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }, [handleFile])

  const onSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) handleFile(f)
  }, [handleFile])

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
      onDragLeave={() => setDragOver(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
      className={cn(
        "relative flex flex-col items-center justify-center w-full p-8 border-2 border-dashed rounded-xl cursor-pointer transition-colors",
        dragOver
          ? "border-accent-500 bg-accent-500/5"
          : "border-border hover:border-accent-500/50 hover:bg-base-900/50",
        uploading && "pointer-events-none"
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={onSelect}
      />

      {uploading ? (
        <>
          <Loader2 className="h-8 w-8 text-accent-400 animate-spin" />
          <p className="mt-3 text-sm text-muted-foreground">Uploading {file?.name}...</p>
        </>
      ) : file ? (
        <>
          <File className="h-8 w-8 text-accent-400" />
          <p className="mt-3 text-sm text-foreground">{file.name}</p>
          <button
            onClick={(e) => { e.stopPropagation(); setFile(null) }}
            className="absolute top-2 right-2 p-1 rounded-full hover:bg-white/10"
          >
            <X className="h-4 w-4 text-muted-foreground" />
          </button>
        </>
      ) : (
        <>
          <Upload className="h-8 w-8 text-muted-foreground" />
          <p className="mt-3 text-sm text-muted-foreground">
            <span className="text-accent-400">Click to upload</span> or drag and drop
          </p>
          <p className="text-xs text-muted-foreground mt-1">PDF, DOCX, XLSX, TXT, MD up to 10MB</p>
        </>
      )}
    </div>
  )
}
