'use client'

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Eye, Layers, ChevronLeft, ChevronRight, Maximize2,
  Minimize2, Grid3X3, MonitorPlay, Info, X, ZoomIn, ZoomOut
} from 'lucide-react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface SliceData {
  instance_number: number
  image: string
}

interface SeriesPreview {
  series_uid: string
  series_description: string
  sequence_type: string | null
  modality: string
  num_slices: number
  slices: SliceData[]
}

interface PreviewData {
  study_id: string
  patient_id: string
  study_date: string | null
  study_description: string | null
  series: SeriesPreview[]
}

interface DicomViewerProps {
  studyId: string
}

const SEQUENCE_COLORS: Record<string, { bg: string; border: string; text: string; dot: string }> = {
  T1: { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-400', dot: 'bg-blue-500' },
  T1c: { bg: 'bg-amber-500/10', border: 'border-amber-500/30', text: 'text-amber-400', dot: 'bg-amber-500' },
  T2: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-400', dot: 'bg-emerald-500' },
  FLAIR: { bg: 'bg-purple-500/10', border: 'border-purple-500/30', text: 'text-purple-400', dot: 'bg-purple-500' },
}

const DEFAULT_COLOR = { bg: 'bg-gray-500/10', border: 'border-gray-500/30', text: 'text-gray-400', dot: 'bg-gray-500' }

export default function DicomViewer({ studyId }: DicomViewerProps) {
  const [previewData, setPreviewData] = useState<PreviewData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeSeries, setActiveSeries] = useState(0)
  const [activeSlice, setActiveSlice] = useState(0)
  const [viewMode, setViewMode] = useState<'single' | 'grid'>('single')
  const [fullscreen, setFullscreen] = useState(false)
  const [zoom, setZoom] = useState(1)
  const [isPlaying, setIsPlaying] = useState(false)

  // Fetch preview data
  useEffect(() => {
    const fetchPreviews = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await axios.get(`${API_URL}/api/preview/${studyId}`)
        setPreviewData(res.data)
        setActiveSeries(0)
        setActiveSlice(0)
      } catch (err: any) {
        console.error('Preview fetch error:', err)
        setError(err.response?.data?.detail || 'Failed to load DICOM previews')
      } finally {
        setLoading(false)
      }
    }
    fetchPreviews()
  }, [studyId])

  // Auto-play slice animation
  useEffect(() => {
    if (!isPlaying || !previewData) return
    const series = previewData.series[activeSeries]
    if (!series) return

    const interval = setInterval(() => {
      setActiveSlice(prev => {
        if (prev >= series.num_slices - 1) {
          setIsPlaying(false)
          return 0
        }
        return prev + 1
      })
    }, 200)

    return () => clearInterval(interval)
  }, [isPlaying, activeSeries, previewData])

  // Keyboard controls
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!previewData) return
      const series = previewData.series[activeSeries]
      if (!series) return

      switch (e.key) {
        case 'ArrowLeft':
          e.preventDefault()
          setActiveSlice(prev => Math.max(0, prev - 1))
          break
        case 'ArrowRight':
          e.preventDefault()
          setActiveSlice(prev => Math.min(series.num_slices - 1, prev + 1))
          break
        case 'ArrowUp':
          e.preventDefault()
          setActiveSeries(prev => Math.max(0, prev - 1))
          setActiveSlice(0)
          break
        case 'ArrowDown':
          e.preventDefault()
          setActiveSeries(prev => Math.min(previewData.series.length - 1, prev + 1))
          setActiveSlice(0)
          break
        case ' ':
          e.preventDefault()
          setIsPlaying(prev => !prev)
          break
        case 'Escape':
          setFullscreen(false)
          break
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [previewData, activeSeries])

  const getColor = (seqType: string | null) => {
    if (!seqType) return DEFAULT_COLOR
    return SEQUENCE_COLORS[seqType] || DEFAULT_COLOR
  }

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-[#1e293b]/50 backdrop-blur-xl rounded-3xl border border-white/10 p-12"
      >
        <div className="flex flex-col items-center gap-4">
          <div className="relative w-16 h-16">
            <div className="absolute inset-0 border-4 border-blue-500/20 rounded-full" />
            <div className="absolute inset-0 border-4 border-transparent border-t-blue-500 rounded-full animate-spin" />
            <Eye className="absolute inset-0 m-auto w-6 h-6 text-blue-400" />
          </div>
          <p className="text-gray-400 font-medium">Loading DICOM images...</p>
        </div>
      </motion.div>
    )
  }

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-[#1e293b]/50 backdrop-blur-xl rounded-3xl border border-red-500/20 p-8"
      >
        <p className="text-red-400 text-center">{error}</p>
      </motion.div>
    )
  }

  if (!previewData || previewData.series.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-[#1e293b]/50 backdrop-blur-xl rounded-3xl border border-white/10 p-8"
      >
        <p className="text-gray-400 text-center">No DICOM image data available for preview.</p>
      </motion.div>
    )
  }

  const currentSeries = previewData.series[activeSeries]
  const currentSlice = currentSeries?.slices[activeSlice]
  const totalSlices = currentSeries?.num_slices || 0
  const color = getColor(currentSeries?.sequence_type)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-[#1e293b]/50 backdrop-blur-xl rounded-3xl border border-white/10 overflow-hidden ${fullscreen ? 'fixed inset-4 z-50 shadow-2xl' : ''
        }`}
    >
      {/* Fullscreen Overlay */}
      {fullscreen && (
        <div className="fixed inset-0 bg-black/80 -z-10" onClick={() => setFullscreen(false)} />
      )}

      {/* Header */}
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-cyan-500/20 rounded-xl border border-cyan-500/30">
              <Eye className="w-6 h-6 text-cyan-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">DICOM Image Viewer</h3>
              <p className="text-sm text-gray-400 mt-0.5">
                {previewData.series.length} sequences &bull; {previewData.series.reduce((s, sr) => s + sr.num_slices, 0)} total slices
                {previewData.patient_id && previewData.patient_id !== 'ANONYMOUS' && (
                  <span> &bull; Patient: {previewData.patient_id}</span>
                )}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* View Mode Toggle */}
            <button
              onClick={() => setViewMode(prev => prev === 'single' ? 'grid' : 'single')}
              className={`p-2 rounded-lg border transition-all ${viewMode === 'grid'
                ? 'bg-blue-500/20 border-blue-500/30 text-blue-400'
                : 'bg-white/5 border-white/10 text-gray-400 hover:text-white'
                }`}
              title={viewMode === 'single' ? 'Grid View' : 'Single View'}
            >
              <Grid3X3 className="w-5 h-5" />
            </button>

            {/* Fullscreen Toggle */}
            <button
              onClick={() => setFullscreen(prev => !prev)}
              className="p-2 rounded-lg bg-white/5 border border-white/10 text-gray-400 hover:text-white transition-all"
              title={fullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
            >
              {fullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row">
        {/* Series Tabs (sidebar) */}
        <div className="lg:w-56 border-b lg:border-b-0 lg:border-r border-white/10 p-4">
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-2">
            MRI Sequences
          </h4>
          <div className="flex lg:flex-col gap-2 overflow-x-auto lg:overflow-x-visible">
            {previewData.series.map((series, idx) => {
              const c = getColor(series.sequence_type)
              const isActive = idx === activeSeries
              return (
                <button
                  key={series.series_uid}
                  onClick={() => { setActiveSeries(idx); setActiveSlice(0); setIsPlaying(false) }}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all whitespace-nowrap lg:w-full ${isActive
                    ? `${c.bg} ${c.border} border`
                    : 'hover:bg-white/5 border border-transparent'
                    }`}
                >
                  <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${isActive ? c.dot : 'bg-gray-600'}`} />
                  <div className="min-w-0">
                    <p className={`text-sm font-bold truncate ${isActive ? c.text : 'text-gray-300'}`}>
                      {series.sequence_type || 'Unknown'}
                    </p>
                    <p className="text-[10px] text-gray-500 truncate">
                      {series.num_slices} slices
                    </p>
                  </div>
                </button>
              )
            })}
          </div>

          {/* Study Info */}
          {previewData.study_description && (
            <div className="hidden lg:block mt-6 p-3 rounded-xl bg-white/5 border border-white/5">
              <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">Study</p>
              <p className="text-xs text-gray-300 leading-relaxed">{previewData.study_description}</p>
              {previewData.study_date && (
                <p className="text-[10px] text-gray-500 mt-2">
                  Date: {previewData.study_date.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3')}
                </p>
              )}
            </div>
          )}
        </div>

        {/* Main Viewer Area */}
        <div className="flex-1 p-6">
          {viewMode === 'single' ? (
            /* Single Slice View */
            <div>
              {/* Image Display */}
              <div className="relative group rounded-2xl overflow-hidden bg-black border border-white/10 mb-4">
                {currentSlice && (
                  <motion.img
                    key={`${activeSeries}-${activeSlice}`}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.15 }}
                    src={`data:image/png;base64,${currentSlice.image}`}
                    alt={`${currentSeries.series_description} - Slice ${activeSlice + 1}`}
                    className="w-full max-h-[500px] object-contain mx-auto"
                    style={{ transform: `scale(${zoom})` }}
                    draggable={false}
                  />
                )}

                {/* Overlay Info */}
                <div className="absolute top-3 left-3 flex flex-col gap-1.5">
                  <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold ${color.bg} ${color.text} backdrop-blur-sm border ${color.border}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${color.dot}`} />
                    {currentSeries.sequence_type || currentSeries.series_description}
                  </span>
                  <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-[10px] font-medium text-gray-300 bg-black/60 backdrop-blur-sm border border-white/10">
                    {currentSeries.modality} &bull; 256 × 256
                  </span>
                </div>

                <div className="absolute top-3 right-3 flex flex-col gap-1.5">
                  <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold text-white bg-black/60 backdrop-blur-sm border border-white/10">
                    {activeSlice + 1} / {totalSlices}
                  </span>
                </div>

                {/* Zoom Controls */}
                <div className="absolute bottom-3 right-3 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => setZoom(z => Math.max(0.5, z - 0.25))}
                    className="p-1.5 rounded-lg bg-black/60 backdrop-blur-sm border border-white/10 text-gray-300 hover:text-white transition-colors"
                  >
                    <ZoomOut className="w-4 h-4" />
                  </button>
                  <span className="px-2 py-1 rounded-lg bg-black/60 backdrop-blur-sm border border-white/10 text-[10px] text-gray-300 font-mono">
                    {Math.round(zoom * 100)}%
                  </span>
                  <button
                    onClick={() => setZoom(z => Math.min(3, z + 0.25))}
                    className="p-1.5 rounded-lg bg-black/60 backdrop-blur-sm border border-white/10 text-gray-300 hover:text-white transition-colors"
                  >
                    <ZoomIn className="w-4 h-4" />
                  </button>
                </div>

                {/* Navigation Arrows */}
                {activeSlice > 0 && (
                  <button
                    onClick={() => setActiveSlice(prev => prev - 1)}
                    className="absolute left-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black/50 backdrop-blur-sm border border-white/10 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/70"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                )}
                {activeSlice < totalSlices - 1 && (
                  <button
                    onClick={() => setActiveSlice(prev => prev + 1)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black/50 backdrop-blur-sm border border-white/10 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/70"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                )}
              </div>

              {/* Slice Slider */}
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setIsPlaying(prev => !prev)}
                  className={`p-2.5 rounded-xl border transition-all ${isPlaying
                    ? 'bg-blue-500/20 border-blue-500/30 text-blue-400'
                    : 'bg-white/5 border-white/10 text-gray-400 hover:text-white'
                    }`}
                  title={isPlaying ? 'Pause' : 'Play through slices'}
                >
                  <MonitorPlay className="w-5 h-5" />
                </button>

                <div className="flex-1 relative">
                  <input
                    type="range"
                    min={0}
                    max={totalSlices - 1}
                    value={activeSlice}
                    onChange={(e) => { setActiveSlice(Number(e.target.value)); setIsPlaying(false) }}
                    className="w-full h-2 rounded-full appearance-none cursor-pointer bg-gray-700/50 accent-blue-500
                      [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4
                      [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-blue-500 [&::-webkit-slider-thumb]:shadow-lg
                      [&::-webkit-slider-thumb]:shadow-blue-500/50 [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-white/20
                      [&::-webkit-slider-thumb]:hover:scale-125 [&::-webkit-slider-thumb]:transition-transform"
                  />
                  {/* Slice position indicator */}
                  <div className="flex justify-between mt-1.5">
                    <span className="text-[10px] text-gray-500">Slice 1</span>
                    <span className="text-[10px] text-gray-500">Slice {totalSlices}</span>
                  </div>
                </div>

                <span className="text-sm font-mono text-gray-300 tabular-nums min-w-[5ch] text-right">
                  {activeSlice + 1}/{totalSlices}
                </span>
              </div>

              {/* Keyboard Hint */}
              <div className="mt-4 flex items-center justify-center gap-4 text-[10px] text-gray-600">
                <span className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10 font-mono">&larr;</kbd>
                  <kbd className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10 font-mono">&rarr;</kbd>
                  Navigate slices
                </span>
                <span className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10 font-mono">&uarr;</kbd>
                  <kbd className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10 font-mono">&darr;</kbd>
                  Switch sequence
                </span>
                <span className="flex items-center gap-1">
                  <kbd className="px-2.5 py-0.5 rounded bg-white/5 border border-white/10 font-mono">Space</kbd>
                  Play/Pause
                </span>
              </div>
            </div>
          ) : (
            /* Grid View - Show all 4 sequences side by side at same slice position */
            <div>
              <div className="grid grid-cols-2 gap-4">
                {previewData.series.map((series, sIdx) => {
                  const c = getColor(series.sequence_type)
                  const sliceIdx = Math.min(activeSlice, series.num_slices - 1)
                  const slice = series.slices[sliceIdx]
                  return (
                    <motion.div
                      key={series.series_uid}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: sIdx * 0.05 }}
                      className={`relative rounded-2xl overflow-hidden bg-black border cursor-pointer transition-all ${sIdx === activeSeries
                        ? `${c.border} border-2 shadow-lg`
                        : 'border-white/10 hover:border-white/20'
                        }`}
                      onClick={() => { setActiveSeries(sIdx); setViewMode('single') }}
                    >
                      {slice && (
                        <img
                          src={`data:image/png;base64,${slice.image}`}
                          alt={`${series.series_description} - Slice ${sliceIdx + 1}`}
                          className="w-full aspect-square object-contain"
                          draggable={false}
                        />
                      )}
                      <div className="absolute bottom-0 inset-x-0 p-3 bg-gradient-to-t from-black/90 to-transparent">
                        <div className="flex items-center justify-between">
                          <span className={`text-sm font-bold ${c.text}`}>
                            {series.sequence_type || series.series_description}
                          </span>
                          <span className="text-[10px] text-gray-400 font-mono">
                            {sliceIdx + 1}/{series.num_slices}
                          </span>
                        </div>
                      </div>
                    </motion.div>
                  )
                })}
              </div>

              {/* Grid Slice Slider */}
              <div className="mt-4 flex items-center gap-4">
                <button
                  onClick={() => setIsPlaying(prev => !prev)}
                  className={`p-2.5 rounded-xl border transition-all ${isPlaying
                    ? 'bg-blue-500/20 border-blue-500/30 text-blue-400'
                    : 'bg-white/5 border-white/10 text-gray-400 hover:text-white'
                    }`}
                >
                  <MonitorPlay className="w-5 h-5" />
                </button>
                <input
                  type="range"
                  min={0}
                  max={Math.max(...previewData.series.map(s => s.num_slices - 1))}
                  value={activeSlice}
                  onChange={(e) => { setActiveSlice(Number(e.target.value)); setIsPlaying(false) }}
                  className="flex-1 h-2 rounded-full appearance-none cursor-pointer bg-gray-700/50 accent-blue-500
                    [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4
                    [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-blue-500"
                />
                <span className="text-sm font-mono text-gray-300 tabular-nums">
                  Slice {activeSlice + 1}
                </span>
              </div>

              <p className="text-center text-[10px] text-gray-600 mt-3">
                Click any image to view full size
              </p>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
