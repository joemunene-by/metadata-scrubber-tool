import React, { useState, useCallback } from 'react';
import {
  ShieldCheck,
  Upload,
  Trash2,
  Download,
  Info,
  FileCheck,
  AlertCircle,
  Zap
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { scrubImage, getMetadata } from './utils/scrubber';
import confetti from 'canvas-confetti';

const App = () => {
  const [files, setFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFileUpload = async (event) => {
    const uploadedFiles = Array.from(event.target.files || event.dataTransfer.files);

    const processedFiles = await Promise.all(
      uploadedFiles.map(async (file) => {
        const metadata = await getMetadata(file);
        return {
          id: Math.random().toString(36).substr(2, 9),
          file,
          metadata: metadata || null,
          status: 'pending',
          cleanedFile: null
        };
      })
    );

    setFiles((prev) => [...prev, ...processedFiles]);
  };

  const removeFile = (id) => {
    setFiles((prev) => prev.filter(f => f.id !== id));
  };

  const cleanFiles = async () => {
    setIsProcessing(true);
    const updatedFiles = await Promise.all(
      files.map(async (item) => {
        if (item.status === 'completed') return item;
        try {
          const cleaned = await scrubImage(item.file);
          return { ...item, status: 'completed', cleanedFile: cleaned };
        } catch (err) {
          return { ...item, status: 'error' };
        }
      })
    );
    setFiles(updatedFiles);
    setIsProcessing(false);
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 },
      colors: ['#6366f1', '#f43f5e', '#ffffff']
    });
  };

  const downloadFile = (item) => {
    const url = URL.createObjectURL(item.cleanedFile);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cleaned_${item.file.name}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-12 md:py-20 lg:py-24">
      {/* Header Section */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-16"
      >
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm font-medium mb-6">
          <Zap size={14} className="fill-primary" />
          <span>Local-First & Secure</span>
        </div>
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 bg-gradient-to-b from-white to-white/60 bg-clip-text text-transparent">
          MetaClean Pro
        </h1>
        <p className="text-lg text-white/50 max-w-2xl mx-auto leading-relaxed">
          The ultimate high-end metadata sanitizer. Strip hidden GPS coordinates, device info, and
          personal signatures from your files entirely in your browser.
        </p>
      </motion.header>

      {/* Main Action Area */}
      <main className="space-y-8">
        {/* Upload Zone */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setIsDragOver(false); handleFileUpload(e); }}
          className={`relative glass-card p-12 text-center border-2 border-dashed transition-all duration-300 ${isDragOver ? 'border-primary bg-primary/5 scale-[1.01]' : 'border-white/10 hover:border-white/20'
            }`}
        >
          <input
            type="file"
            multiple
            onChange={handleFileUpload}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          <div className="flex flex-col items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center text-primary">
              <Upload size={32} />
            </div>
            <div>
              <p className="text-xl font-semibold mb-1">Drop your files here</p>
              <p className="text-white/40">Support for JPEG, PNG, and HEIC up to 50MB</p>
            </div>
          </div>
        </motion.div>

        {/* Files List */}
        <AnimatePresence mode="popLayout">
          {files.length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              <div className="flex items-center justify-between mb-2 px-2">
                <h2 className="text-sm font-semibold uppercase tracking-wider text-white/40">
                  Ready to process ({files.length})
                </h2>
                {files.some(f => f.status === 'pending') && (
                  <button
                    onClick={cleanFiles}
                    disabled={isProcessing}
                    className="premium-button py-2 px-4 flex items-center gap-2"
                  >
                    {isProcessing ? (
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <ShieldCheck size={18} />
                    )}
                    {isProcessing ? 'Processing...' : 'Secure All Files'}
                  </button>
                )}
              </div>

              {files.map((item) => (
                <motion.div
                  key={item.id}
                  layout
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className="glass-card p-4 flex items-center gap-4"
                >
                  <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center text-white/40 flex-shrink-0">
                    <FileCheck size={24} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{item.file.name}</p>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-xs text-white/30 truncate">
                        {(item.file.size / 1024 / 1024).toFixed(2)} MB • {item.file.type}
                      </span>
                      {item.metadata && (
                        <div className="flex items-center gap-1 text-[10px] bg-accent/10 text-accent px-1.5 py-0.5 rounded uppercase font-bold">
                          <AlertCircle size={10} />
                          Metadata Detected
                        </div>
                      )}
                    </div>

                    {/* Metadata Preview */}
                    {item.metadata && item.status === 'pending' && (
                      <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-2">
                        {Object.entries(item.metadata).slice(0, 4).map(([key, val]) => (
                          <div key={key} className="text-[10px] text-white/20 bg-white/5 p-1 px-2 rounded truncate">
                            <span className="font-semibold text-white/40">{key}:</span> {val}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    {item.status === 'completed' ? (
                      <button
                        onClick={() => downloadFile(item)}
                        className="p-2 text-primary hover:bg-primary/10 rounded-lg transition-colors"
                        title="Download Cleaned File"
                      >
                        <Download size={20} />
                      </button>
                    ) : (
                      <button
                        disabled={isProcessing}
                        onClick={() => removeFile(item.id)}
                        className="p-2 text-white/20 hover:text-white/40 hover:bg-white/5 rounded-lg transition-colors"
                      >
                        <Trash2 size={20} />
                      </button>
                    )}
                  </div>
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Footer Info */}
      <footer className="mt-32 pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between gap-6 text-white/30 text-sm">
        <div className="flex items-center gap-2">
          <ShieldCheck size={18} className="text-primary" />
          <span>Files are never uploaded. Privacy by design.</span>
        </div>
        <div className="flex items-center gap-6">
          <a href="#" className="hover:text-white transition-colors">Documentation</a>
          <a href="#" className="hover:text-white transition-colors">CLI Tool</a>
          <a href="#" className="hover:text-white transition-colors">GitHub</a>
        </div>
      </footer>
    </div>
  );
};

export default App;
