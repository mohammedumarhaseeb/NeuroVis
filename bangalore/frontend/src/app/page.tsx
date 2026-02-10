'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useInView } from 'react-intersection-observer'
import FileUpload from '@/components/FileUpload'
import ValidationStatus from '@/components/ValidationStatus'
import AnalysisResults from '@/components/AnalysisResults'
import DicomViewer from '@/components/DicomViewer'
import { Brain, Shield, Zap, CheckCircle2, Sparkles, Activity, ArrowRight, Upload, BarChart3, Lock } from 'lucide-react'

// Animation variants
const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
}

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2
    }
  }
}

export default function Home() {
  const [studyId, setStudyId] = useState<string | null>(null)
  const [validationData, setValidationData] = useState<any>(null)
  const [analysisResults, setAnalysisResults] = useState<any>(null)
  const [scrolled, setScrolled] = useState(false)

  // Scroll handler for navbar
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const handleUploadComplete = (uploadedStudyId: string, validation: any) => {
    setStudyId(uploadedStudyId)
    setValidationData(validation)
    setAnalysisResults(null)
    // Smooth scroll to validation section
    setTimeout(() => {
      document.getElementById('analysis-section')?.scrollIntoView({ behavior: 'smooth' })
    }, 500)
  }

  const handleAnalysisComplete = (results: any) => {
    setAnalysisResults(results)
  }

  const resetApp = () => {
    setStudyId(null)
    setValidationData(null)
    setAnalysisResults(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="min-h-screen bg-[#0f172a] text-white overflow-x-hidden selection:bg-blue-500/30">

      {/* Dynamic Background */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-blue-600/10 blur-[120px] animate-pulse-slow" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-cyan-600/10 blur-[120px] animate-pulse-slow delay-1000" />
        <div className="absolute top-[40%] left-[40%] w-[20%] h-[20%] rounded-full bg-purple-600/10 blur-[100px] animate-pulse-slow delay-2000" />
      </div>

      {/* Navigation */}
      <nav className={`fixed w-full z-50 transition-all duration-300 ${scrolled ? 'bg-[#0f172a]/80 backdrop-blur-md border-b border-white/10 py-4' : 'bg-transparent py-6'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 cursor-pointer group" onClick={resetApp}>
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-xl blur opacity-75 group-hover:opacity-100 transition-opacity"></div>
                <div className="relative p-2.5 bg-[#0f172a] border border-white/10 rounded-xl group-hover:scale-105 transition-transform duration-300">
                  <Brain className="w-6 h-6 text-blue-400 group-hover:text-blue-300" />
                </div>
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                  NeuroVision AI
                </h1>
                <p className="text-[10px] text-gray-400 font-medium tracking-wider uppercase">Medical Grade Analysis</p>
              </div>
            </div>

            <div className="flex items-center gap-6">
              <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></div>
                <span className="text-xs text-emerald-400 font-medium">System Operational</span>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <AnimatePresence>
        {!studyId && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, height: 0 }}
            className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 px-4"
          >
            <div className="max-w-7xl mx-auto text-center relative z-10">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm font-medium mb-8 backdrop-blur-sm"
              >
                <Sparkles className="w-4 h-4" />
                <span>Next-Generation Medical AI</span>
              </motion.div>

              <motion.h1
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 }}
                className="text-5xl md:text-7xl font-bold tracking-tight mb-8"
              >
                Advanced Brain Tumor
                <span className="block mt-2 bg-gradient-to-r from-blue-400 via-cyan-400 to-purple-400 bg-clip-text text-transparent animate-gradient">
                  MRI Analysis Platform
                </span>
              </motion.h1>

              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                className="text-xl text-gray-400 max-w-3xl mx-auto mb-12 leading-relaxed"
              >
                The first validation-gated AI system for precise tumor segmentation and
                genotype prediction. Built with safety-first architecture.
              </motion.p>

              {/* Stats Grid */}
              <motion.div
                variants={staggerContainer}
                initial="hidden"
                animate="visible"
                className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto mb-16"
              >
                {[
                  { label: "Dice Score", value: "92.3%", icon: Activity },
                  { label: "Inference", value: "< 2s", icon: Zap },
                  { label: "Sequences", value: "3", icon: BarChart3 },
                  { label: "Security", value: "HIPAA", icon: Lock },
                ].map((stat, index) => (
                  <motion.div
                    key={index}
                    variants={fadeIn}
                    className="p-4 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm hover:bg-white/10 transition-colors"
                  >
                    <div className="text-2xl font-bold text-white mb-1">{stat.value}</div>
                    <div className="text-sm text-gray-400 flex items-center justify-center gap-1.5">
                      {/* Note: Icon rendering simplified for map */}
                      {stat.label}
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Analysis Section */}
      <main id="analysis-section" className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-32">
        <motion.div
          layout
          className="bg-[#1e293b]/50 backdrop-blur-xl border border-white/10 rounded-3xl overflow-hidden shadow-2xl"
        >
          {/* Header for Analysis Card */}
          <div className="p-8 border-b border-white/10">
            <h2 className="text-2xl font-bold flex items-center gap-3">
              <Upload className="w-6 h-6 text-blue-400" />
              MRI Study Analysis
            </h2>
            <p className="text-gray-400 mt-2">
              Upload DICOM files or ZIP archive to begin analysis. Validation is performed automatically.
            </p>
          </div>

          <div className="p-8">
            {/* Upload Area */}
            <div className={`transition-all duration-500 ${studyId ? 'mb-12' : ''}`}>
              <FileUpload onUploadComplete={handleUploadComplete} />
            </div>

            {/* Validation & Results */}
            <AnimatePresence mode="wait">
              {validationData && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="space-y-8"
                >
                  {/* DICOM Image Viewer */}
                  <DicomViewer studyId={studyId!} />

                  <ValidationStatus
                    studyId={studyId!}
                    validationData={validationData}
                    onAnalysisComplete={handleAnalysisComplete}
                  />

                  {analysisResults && (
                    <motion.div
                      initial={{ opacity: 0, y: 40 }}
                      animate={{ opacity: 1, y: 0 }}
                    >
                      <AnalysisResults results={analysisResults} />
                    </motion.div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* Features Section - Below Fold */}
        {!studyId && (
          <div className="mt-32 grid md:grid-cols-3 gap-8">
            {[
              {
                title: "Medical Gatekeeper",
                desc: "Strict validation ensures only complete studies with all required sequences proceed to analysis.",
                icon: Shield,
                color: "blue"
              },
              {
                title: "Deep Learning Core",
                desc: "State-of-the-art segmentation and classification models trained on BraTS datasets.",
                icon: Brain,
                color: "cyan"
              },
              {
                title: "Explainable AI",
                desc: "Transparency first. Visual attention maps and clear reasoning for every prediction.",
                icon: Sparkles,
                color: "purple"
              }
            ].map((feature, idx) => (
              <div key={idx} className="group p-8 rounded-3xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all duration-300 hover:-translate-y-2">
                <div className={`w-14 h-14 rounded-2xl bg-${feature.color}-500/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform`}>
                  <feature.icon className={`w-7 h-7 text-${feature.color}-400`} />
                </div>
                <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                <p className="text-gray-400 leading-relaxed">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 py-12 bg-[#0f172a] relative z-20">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-gray-400 text-sm mb-4">
            NeuroVision AI • Research Prototype v1.0
          </p>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-500/10 border border-orange-500/20 text-orange-400 text-xs">
            <span>⚠️ Not for Clinical Use</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
