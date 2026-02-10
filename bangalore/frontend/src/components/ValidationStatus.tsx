'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle2, XCircle, AlertTriangle, Play, FileText, Info, Activity } from 'lucide-react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ValidationStatusProps {
  studyId: string
  validationData: any
  onAnalysisComplete: (results: any) => void
}

export default function ValidationStatus({
  studyId,
  validationData,
  onAnalysisComplete
}: ValidationStatusProps) {
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showBypassWarning, setShowBypassWarning] = useState(false)

  const validation = validationData.validation
  const isValid = validation.is_valid

  const runInference = async (bypassValidation: boolean = false) => {
    setRunning(true)
    setError(null)

    try {
      const response = await axios.post(`${API_URL}/api/inference`, {
        study_id: studyId,
        run_segmentation: true,
        run_genotype_prediction: true,
        generate_explanations: true,
        bypass_validation: bypassValidation,
      })

      onAnalysisComplete(response.data)
      setShowBypassWarning(false)
    } catch (err: any) {
      console.error('Inference error:', err)
      setError(
        err.response?.data?.detail?.error ||
        err.response?.data?.detail ||
        'Analysis failed. Please try again.'
      )
    } finally {
      setRunning(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-[#1e293b]/50 backdrop-blur-sm rounded-3xl border border-white/10 overflow-hidden"
    >
      <div className="p-8">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <FileText className="w-6 h-6 text-blue-400" />
            Medical Validation
          </h2>
          <div className="text-xs text-gray-500 font-mono bg-black/20 px-3 py-1 rounded-full">
            ID: {studyId.slice(0, 8)}...
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          {/* Overall Status Card */}
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className={`relative overflow-hidden rounded-2xl p-6 border transition-all duration-300 h-full flex flex-col justify-center ${isValid
              ? 'bg-emerald-500/10 border-emerald-500/20 shadow-lg shadow-emerald-500/10'
              : 'bg-red-500/10 border-red-500/20 shadow-lg shadow-red-500/10'
              }`}
          >
            <div className="flex items-start gap-5 relative z-10">
              <div className={`p-3 rounded-xl ${isValid ? 'bg-emerald-500/20' : 'bg-red-500/20'}`}>
                {isValid ? (
                  <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                ) : (
                  <XCircle className="w-8 h-8 text-red-400" />
                )}
              </div>
              <div className="flex-1">
                <h3 className={`text-xl font-bold mb-2 ${isValid ? 'text-emerald-400' : 'text-red-400'}`}>
                  {isValid ? 'Validation Passed' : 'Validation Failed'}
                </h3>
                <p className={`text-sm leading-relaxed ${isValid ? 'text-emerald-200/80' : 'text-red-200/80'}`}>
                  {validationData.summary}
                </p>
              </div>
            </div>

            {/* Background Glow */}
            <div className={`absolute top-0 right-0 w-64 h-64 rounded-full blur-[80px] -translate-y-1/2 translate-x-1/2 opacity-20 ${isValid ? 'bg-emerald-500' : 'bg-red-500'
              }`} />
          </motion.div>

          {/* MRI Scan Preview */}
          <AnimatePresence>
            {validation.preview_image && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="relative group rounded-2xl overflow-hidden border border-white/10 bg-black/40"
              >
                <img
                  src={`data:image/png;base64,${validation.preview_image}`}
                  alt="MRI Scan Preview"
                  className="w-full h-48 object-cover opacity-80 group-hover:opacity-100 transition-opacity duration-500"
                />
                <div className="absolute inset-x-0 bottom-0 p-3 bg-gradient-to-t from-black/80 to-transparent">
                  <div className="flex items-center gap-2 text-xs font-medium text-white/80">
                    <Activity className="w-3.5 h-3.5 text-blue-400" />
                    Preview Scan • Anatomical Reference
                  </div>
                </div>
                <div className="absolute top-3 right-3 px-2 py-1 rounded bg-blue-500/20 border border-blue-500/30 backdrop-blur-md text-[10px] font-bold text-blue-400 uppercase tracking-widest">
                  Live Preview
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Required Sequences Grid */}
        <div className="mb-8">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Info className="w-4 h-4" />
            Required Sequences
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(validation.required_sequences).map(([seq, present]: [string, any], idx) => (
              <motion.div
                key={seq}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className={`flex items-center gap-3 p-4 rounded-xl border backdrop-blur-sm transition-all ${present
                  ? 'bg-emerald-500/5 border-emerald-500/20 text-emerald-400'
                  : 'bg-red-500/5 border-red-500/20 text-red-400'
                  }`}
              >
                {present ? (
                  <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                ) : (
                  <XCircle className="w-5 h-5 flex-shrink-0" />
                )}
                <span className="font-semibold">{seq}</span>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Errors & Warnings */}
        <AnimatePresence>
          {(validation.errors.length > 0 || validation.warnings.length > 0) && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              className="space-y-4 mb-8"
            >
              {validation.errors.map((error: string, idx: number) => (
                <div key={idx} className="flex items-start gap-3 p-4 rounded-xl bg-red-500/5 border border-red-500/20 text-red-400">
                  <XCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <span className="text-sm">{error}</span>
                </div>
              ))}
              {validation.warnings.map((warning: string, idx: number) => (
                <div key={idx} className="flex items-start gap-3 p-4 rounded-xl bg-orange-500/5 border border-orange-500/20 text-orange-400">
                  <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <span className="text-sm">{warning}</span>
                </div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Action Buttons */}
        <div className="mt-8 pt-8 border-t border-white/10">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => runInference(false)}
            disabled={!isValid || running}
            className={`w-full py-5 rounded-2xl font-bold text-lg shadow-lg relative overflow-hidden group ${!isValid || running
              ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
              : 'bg-gradient-to-r from-blue-600 via-cyan-600 to-blue-600 bg-[length:200%_100%] animate-shimmer text-white hover:shadow-cyan-500/25'
              }`}
          >
            <div className="relative z-10 flex items-center justify-center gap-3">
              {running ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Processing Study...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5 fill-current" />
                  Run AI Analysis
                </>
              )}
            </div>
          </motion.button>
        </div>

        {/* Bypass Options */}
        {!isValid && !showBypassWarning && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-6 text-center"
          >
            <button
              onClick={() => setShowBypassWarning(true)}
              className="text-xs text-orange-400/60 hover:text-orange-400 hover:underline transition-colors"
            >
              Advanced: Force Run (Bypass Validation)
            </button>
          </motion.div>
        )}

        <AnimatePresence>
          {showBypassWarning && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="mt-6 overflow-hidden"
            >
              <div className="p-4 rounded-xl bg-orange-500/10 border border-orange-500/20">
                <div className="flex items-center gap-2 mb-3 text-orange-400 font-bold">
                  <AlertTriangle className="w-5 h-5" />
                  Unsafe Operation Warning
                </div>
                <p className="text-sm text-orange-300/80 mb-4">
                  Forcing analysis on invalid data may produce incorrect or misleading results.
                  This feature is for testing purposes only.
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={() => runInference(true)}
                    className="flex-1 py-2 rounded-lg bg-orange-600 hover:bg-orange-700 text-white text-sm font-medium transition-colors"
                  >
                    Yes, Force Run
                  </button>
                  <button
                    onClick={() => setShowBypassWarning(false)}
                    className="flex-1 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-white text-sm font-medium transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}
