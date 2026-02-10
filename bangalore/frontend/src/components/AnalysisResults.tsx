'use client'

import { motion } from 'framer-motion'
import { Download, AlertTriangle, TrendingUp, Activity, CheckCircle2, XCircle, Sparkles, Brain, Scan } from 'lucide-react'

interface AnalysisResultsProps {
  results: any
}

const ProbabilityBar = ({ label, probability, colorClass }: { label: string; probability: number; colorClass: string }) => {
  const percentage = (probability * 100).toFixed(1)
  const isHigh = probability > 0.5

  return (
    <div className="mb-5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-300">{label}</span>
        <div className="flex items-center gap-2">
          <span className={`text-sm font-bold ${isHigh ? 'text-white' : 'text-gray-400'}`}>{percentage}%</span>
        </div>
      </div>
      <div className="h-2.5 bg-gray-700/50 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          whileInView={{ width: `${percentage}%` }}
          viewport={{ once: true }}
          transition={{ duration: 1, ease: "easeOut" }}
          className={`h-full rounded-full ${colorClass}`}
        />
      </div>
    </div>
  )
}

export default function AnalysisResults({ results }: AnalysisResultsProps) {
  const { segmentation, genotype_prediction, explainability, clinical_flags } = results

  const downloadReport = () => {
    const reportData = {
      study_id: results.study_id,
      timestamp: results.timestamp,
      results
    }

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `neurovision-analysis-${results.study_id.substring(0, 8)}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  }

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  }

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="space-y-8"
    >
      {/* Header Card */}
      <motion.div variants={item} className="bg-[#1e293b]/50 backdrop-blur-xl rounded-3xl p-8 border border-white/10 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-[100px] -translate-y-1/2 translate-x-1/2" />

        <div className="flex flex-col md:flex-row items-center justify-between gap-6 relative z-10">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-500/20 rounded-2xl border border-blue-500/30">
              <Sparkles className="w-8 h-8 text-blue-400" />
            </div>
            <div>
              <h2 className="text-3xl font-bold text-white mb-1">
                Analysis Complete
              </h2>
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                Processed in {results.processing_time_seconds.toFixed(2)}s
              </div>
            </div>
          </div>

          <button
            onClick={downloadReport}
            className="flex items-center gap-2 px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all hover:scale-105 active:scale-95 text-white font-medium group"
          >
            <Download className="w-5 h-5 group-hover:-translate-y-1 transition-transform" />
            Export Report
          </button>
        </div>

        {/* Clinical Flags */}
        {clinical_flags && (clinical_flags.high_risk || clinical_flags.requires_urgent_review) && (
          <motion.div
            initial={{ opacity: 0, marginTop: 0 }}
            animate={{ opacity: 1, marginTop: 24 }}
            className="p-6 bg-red-500/10 border border-red-500/20 rounded-2xl"
          >
            <div className="flex items-start gap-4">
              <div className="p-2 bg-red-500/20 rounded-lg shrink-0">
                <AlertTriangle className="w-6 h-6 text-red-500" />
              </div>
              <div>
                <h3 className="font-bold text-red-400 text-lg mb-2">
                  Clinical Attention Required
                </h3>
                {clinical_flags.high_risk && (
                  <p className="text-red-300 text-sm mb-2 font-medium">
                    • High Risk Indicators Detected
                  </p>
                )}
                {clinical_flags.requires_urgent_review && (
                  <p className="text-red-300 text-sm mb-2">
                    • Urgent Review: {clinical_flags.urgency_reason}
                  </p>
                )}
                {clinical_flags.risk_factors.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {clinical_flags.risk_factors.map((factor: string, idx: number) => (
                      <span key={idx} className="px-3 py-1 bg-red-500/10 border border-red-500/20 rounded-lg text-xs text-red-300">
                        {factor}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Tumor Segmentation */}
        {segmentation && (
          <motion.div variants={item} className="bg-[#1e293b]/50 backdrop-blur-xl rounded-3xl p-8 border border-white/10">
            <div className="flex items-center gap-3 mb-8">
              <div className="p-2 bg-purple-500/20 rounded-xl border border-purple-500/30">
                <Scan className="w-6 h-6 text-purple-400" />
              </div>
              <h3 className="text-xl font-bold text-white">Volumetric Analysis</h3>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-8">
              {[
                { label: 'Whole Tumor', value: segmentation.whole_tumor_volume_ml, color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20' },
                { label: 'Enhancing', value: segmentation.enhancing_tumor_volume_ml, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20' },
                { label: 'Necrotic Core', value: segmentation.necrotic_core_volume_ml, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' },
                { label: 'Edema', value: (segmentation.whole_tumor_volume_ml - segmentation.enhancing_tumor_volume_ml - segmentation.necrotic_core_volume_ml), color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' },
              ].map((stat, idx) => (
                <div key={idx} className={`p-4 rounded-2xl ${stat.bg} border ${stat.border}`}>
                  <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">{stat.label}</p>
                  <p className={`text-2xl font-bold ${stat.color}`}>
                    {stat.value.toFixed(1)} <span className="text-sm text-gray-500">ml</span>
                  </p>
                </div>
              ))}
            </div>

            {segmentation.segmentation_map && (
              <div className="relative group rounded-2xl overflow-hidden border border-white/10">
                <img
                  src={`data:image/png;base64,${segmentation.segmentation_map}`}
                  alt="Segmentation Map"
                  className="w-full h-auto opacity-80 group-hover:opacity-100 transition-opacity"
                />
                <div className="absolute bottom-0 inset-x-0 p-4 bg-gradient-to-t from-black/80 to-transparent">
                  <div className="flex justify-center gap-4 text-xs font-medium">
                    <span className="flex items-center gap-1.5 text-red-300"><span className="w-2 h-2 rounded-full bg-red-500" />Necrotic</span>
                    <span className="flex items-center gap-1.5 text-emerald-300"><span className="w-2 h-2 rounded-full bg-emerald-500" />Edema</span>
                    <span className="flex items-center gap-1.5 text-amber-300"><span className="w-2 h-2 rounded-full bg-amber-500" />Enhancing</span>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* Genotype Prediction */}
        {genotype_prediction && (
          <motion.div variants={item} className="space-y-8">
            <div className="bg-[#1e293b]/50 backdrop-blur-xl rounded-3xl p-8 border border-white/10">
              <div className="flex items-center gap-3 mb-8">
                <div className="p-2 bg-pink-500/20 rounded-xl border border-pink-500/30">
                  <Brain className="w-6 h-6 text-pink-400" />
                </div>
                <h3 className="text-xl font-bold text-white">Genotype Prediction</h3>
              </div>

              <div className="space-y-2">
                <ProbabilityBar
                  label="IDH Mutation"
                  probability={genotype_prediction.idh_mutation_probability}
                  colorClass="bg-gradient-to-r from-blue-500 to-cyan-400"
                />
                <ProbabilityBar
                  label="MGMT Methylation"
                  probability={genotype_prediction.mgmt_methylation_probability}
                  colorClass="bg-gradient-to-r from-emerald-500 to-green-400"
                />
                <ProbabilityBar
                  label="EGFR Amplification"
                  probability={genotype_prediction.egfr_amplification_probability}
                  colorClass="bg-gradient-to-r from-orange-500 to-amber-400"
                />
                <ProbabilityBar
                  label="IDH Wildtype"
                  probability={genotype_prediction.idh_wildtype_probability}
                  colorClass="bg-gradient-to-r from-purple-500 to-pink-400"
                />
              </div>

              <div className="mt-8 pt-6 border-t border-white/10 flex items-center justify-between">
                <span className="text-sm text-gray-400">Model Confidence</span>
                <span className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                  {(genotype_prediction.prediction_confidence * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            {/* Explainability */}
            {explainability && (
              <div className="space-y-6">
                <div className="bg-[#1e293b]/50 backdrop-blur-xl rounded-3xl p-8 border border-white/10">
                  <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <Activity className="w-5 h-5 text-blue-400" />
                    AI Reasoning
                  </h3>

                  <p className="text-gray-300 leading-relaxed text-sm mb-6 bg-white/5 p-4 rounded-xl border border-white/5">
                    {explainability.explanation_text}
                  </p>

                  <div className="flex flex-wrap gap-2">
                    {explainability.important_features?.map((feature: string, idx: number) => (
                      <span key={idx} className="px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-xs text-blue-300 font-medium">
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Grad-CAM Attention Maps */}
                {explainability.attention_maps && Object.keys(explainability.attention_maps).length > 0 && (
                  <div className="bg-[#1e293b]/50 backdrop-blur-xl rounded-3xl p-8 border border-white/10">
                    <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                      <Sparkles className="w-5 h-5 text-amber-400" />
                      Grad-CAM Explainability
                    </h3>

                    <div className="grid grid-cols-2 gap-4">
                      {Object.entries(explainability.attention_maps).map(([seq, base64]: [string, any], idx) => (
                        <div key={idx} className="group relative rounded-2xl overflow-hidden border border-white/10 bg-black/40">
                          <img
                            src={`data:image/png;base64,${base64}`}
                            alt={`Grad-CAM ${seq}`}
                            className="w-full h-auto object-cover opacity-80 group-hover:opacity-100 transition-opacity"
                          />
                          <div className="absolute top-2 left-2 px-2 py-1 bg-black/60 backdrop-blur-md rounded-lg border border-white/10 text-[10px] font-bold text-white uppercase tracking-wider">
                            {seq}
                          </div>
                        </div>
                      ))}
                    </div>
                    <p className="mt-4 text-[10px] text-gray-500 text-center uppercase tracking-widest">
                      Heatmaps indicate regions of high model attention
                    </p>
                  </div>
                )}
              </div>
            )}
          </motion.div>
        )}
      </div>

      {/* Tumor Heatmap Analysis Grid - Full Width */}
      {segmentation && (segmentation.tumor_density_heatmap || segmentation.tumor_region_grid || segmentation.intensity_distribution || segmentation.disease_heatmap) && (
        <motion.div variants={item} className="bg-[#1e293b]/50 backdrop-blur-xl rounded-3xl p-8 border border-white/10">
          <div className="flex items-center gap-3 mb-8">
            <div className="p-2 bg-orange-500/20 rounded-xl border border-orange-500/30">
              <TrendingUp className="w-6 h-6 text-orange-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">Tumor Heatmap Analysis</h3>
              <p className="text-sm text-gray-400 mt-0.5">Advanced visualizations using Seaborn, Matplotlib &amp; SciPy</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Tumor Density Heatmap */}
            {segmentation.tumor_density_heatmap && (
              <div className="group rounded-2xl overflow-hidden border border-white/10 bg-[#0f172a] hover:border-blue-500/30 transition-all duration-300">
                <div className="p-4 border-b border-white/5">
                  <h4 className="text-sm font-bold text-blue-400 uppercase tracking-wider">Tumor Density Map</h4>
                  <p className="text-xs text-gray-500 mt-1">Gaussian kernel density estimation showing tumor concentration</p>
                </div>
                <img
                  src={`data:image/png;base64,${segmentation.tumor_density_heatmap}`}
                  alt="Tumor Density Heatmap"
                  className="w-full h-auto opacity-90 group-hover:opacity-100 transition-opacity"
                />
              </div>
            )}

            {/* Disease Severity Heatmap */}
            {segmentation.disease_heatmap && (
              <div className="group rounded-2xl overflow-hidden border border-white/10 bg-[#0f172a] hover:border-red-500/30 transition-all duration-300">
                <div className="p-4 border-b border-white/5">
                  <h4 className="text-sm font-bold text-red-400 uppercase tracking-wider">Disease Severity Map</h4>
                  <p className="text-xs text-gray-500 mt-1">Color-coded severity zones from low (green) to critical (red)</p>
                </div>
                <img
                  src={`data:image/png;base64,${segmentation.disease_heatmap}`}
                  alt="Disease Severity Heatmap"
                  className="w-full h-auto opacity-90 group-hover:opacity-100 transition-opacity"
                />
              </div>
            )}

            {/* Tumor Region Grid - Full Width */}
            {segmentation.tumor_region_grid && (
              <div className="md:col-span-2 group rounded-2xl overflow-hidden border border-white/10 bg-[#0f172a] hover:border-purple-500/30 transition-all duration-300">
                <div className="p-4 border-b border-white/5">
                  <h4 className="text-sm font-bold text-purple-400 uppercase tracking-wider">Region Analysis Grid</h4>
                  <p className="text-xs text-gray-500 mt-1">4-panel view: Segmentation • Density Contours • Connected Regions • Severity Zones</p>
                </div>
                <img
                  src={`data:image/png;base64,${segmentation.tumor_region_grid}`}
                  alt="Tumor Region Grid Analysis"
                  className="w-full h-auto opacity-90 group-hover:opacity-100 transition-opacity"
                />
              </div>
            )}

            {/* Intensity Distribution - Full Width */}
            {segmentation.intensity_distribution && (
              <div className="md:col-span-2 group rounded-2xl overflow-hidden border border-white/10 bg-[#0f172a] hover:border-emerald-500/30 transition-all duration-300">
                <div className="p-4 border-b border-white/5">
                  <h4 className="text-sm font-bold text-emerald-400 uppercase tracking-wider">Composition Analysis</h4>
                  <p className="text-xs text-gray-500 mt-1">Tumor component distribution breakdown and type percentages</p>
                </div>
                <img
                  src={`data:image/png;base64,${segmentation.intensity_distribution}`}
                  alt="Tumor Composition Analysis"
                  className="w-full h-auto opacity-90 group-hover:opacity-100 transition-opacity"
                />
              </div>
            )}
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}
