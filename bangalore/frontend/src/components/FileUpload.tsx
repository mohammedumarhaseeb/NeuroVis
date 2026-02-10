'use client'

import { useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, File, CheckCircle2, AlertCircle, X, Loader2 } from 'lucide-react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface FileUploadProps {
  onUploadComplete: (studyId: string, validationData: any) => void
}

export default function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [files, setFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isDragActive, setIsDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files))
      setError(null)
    }
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragActive(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragActive(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragActive(false)
    if (e.dataTransfer.files) {
      setFiles(Array.from(e.dataTransfer.files))
      setError(null)
    }
  }, [])

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const clearFiles = () => {
    setFiles([])
    setError(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleUpload = async () => {
    if (files.length === 0) return

    setUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      files.forEach(file => formData.append('files', file))

      const uploadRes = await axios.post(`${API_URL}/api/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      const { study_id } = uploadRes.data

      // Artificial delay for animation
      await new Promise(resolve => setTimeout(resolve, 800))

      const validationRes = await axios.get(`${API_URL}/api/validation/${study_id}`)

      onUploadComplete(study_id, validationRes.data)
    } catch (err: any) {
      console.error('Upload error:', err)
      setError(err.response?.data?.detail || 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="w-full max-w-2xl mx-auto"
    >
      <div
        className={`relative group rounded-3xl border-2 border-dashed transition-all duration-300 p-10 text-center
          ${isDragActive
            ? 'border-blue-500 bg-blue-500/10'
            : files.length > 0
              ? 'border-emerald-500/50 bg-emerald-500/5'
              : 'border-white/20 hover:border-blue-400/50 hover:bg-white/5'
          }
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          multiple
          accept="*"
          className="hidden"
        />

        <div className="flex flex-col items-center gap-4 pointer-events-none">
          <motion.div
            animate={{
              scale: isDragActive ? 1.1 : 1,
              rotate: isDragActive ? 10 : 0
            }}
            className={`relative w-24 h-24 rounded-2xl flex items-center justify-center mb-2 transition-all overflow-hidden
              ${files.length > 0 ? 'bg-emerald-500/20' : 'bg-blue-500/20'}
            `}
          >
            {uploading ? (
              <Loader2 className="w-10 h-10 text-blue-400 animate-spin" />
            ) : files.length > 0 ? (
              <CheckCircle2 className="w-10 h-10 text-emerald-400" />
            ) : (
              <Upload className="w-10 h-10 text-blue-400" />
            )}
          </motion.div>

          {files.length > 0 ? (
            <div className="space-y-1">
              <h3 className="text-xl font-bold text-emerald-400">
                {files.length} Files Selected
              </h3>
              <p className="text-sm text-gray-400">
                Ready to upload. Click to change files.
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              <h3 className="text-xl font-bold text-white">
                Drag & Drop MRI Files
              </h3>
              <p className="text-sm text-gray-400">
                Supports .dcm, .dicom, or .zip archives
              </p>
            </div>
          )}
        </div>

        {/* Floating Particles Animation */}
        {isDragActive && (
          <div className="absolute inset-0 overflow-hidden rounded-3xl pointer-events-none">
            {[...Array(5)].map((_, i) => (
              <motion.div
                key={i}
                initial={{ y: 100, opacity: 0 }}
                animate={{ y: -100, opacity: [0, 1, 0] }}
                transition={{
                  repeat: Infinity,
                  duration: 2,
                  delay: i * 0.2,
                  ease: "linear"
                }}
                className="absolute left-[50%] w-1 h-1 bg-blue-400 rounded-full"
                style={{ left: `${20 + Math.random() * 60}%` }}
              />
            ))}
          </div>
        )}
      </div>

      <AnimatePresence>
        {files.length > 0 && !uploading && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-6 flex gap-4"
          >
            <button
              onClick={(e) => { e.stopPropagation(); clearFiles(); }}
              className="px-6 py-3 rounded-xl font-medium text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
            >
              Clear
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); handleUpload(); }}
              className="flex-1 px-6 py-3 rounded-xl font-bold text-white bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 shadow-lg shadow-blue-500/25 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              Upload and Validate
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading State */}
      {uploading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-8 text-center"
        >
          <div className="w-full max-w-xs mx-auto bg-white/5 rounded-full h-1.5 overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-500 to-cyan-500"
              initial={{ width: "0%" }}
              animate={{ width: "100%" }}
              transition={{ duration: 1.5, ease: "easeInOut" }}
            />
          </div>
          <p className="mt-4 text-sm font-medium text-blue-400 animate-pulse">
            Securely processing medical data...
          </p>
        </motion.div>
      )}

      {/* Error Message */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 flex items-center gap-3"
          >
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <p className="text-sm font-medium">{error}</p>
            <button
              onClick={() => setError(null)}
              className="ml-auto p-1 hover:bg-white/5 rounded-full"
            >
              <X className="w-4 h-4" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
