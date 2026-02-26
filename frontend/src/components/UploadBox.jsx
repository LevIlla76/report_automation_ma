"use client";

import React, { useCallback, useState } from 'react';
import { Upload, FileText, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { Card } from "@/components/ui/card";

export default function UploadBox({ onUpload, label, accept = ".docx" }) {
    const [isDragOver, setIsDragOver] = useState(false);
    const [file, setFile] = useState(null);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        setIsDragOver(false);
        const uploadedFile = e.dataTransfer.files[0];
        if (uploadedFile) {
            setFile(uploadedFile);
            onUpload(uploadedFile);
        }
    }, [onUpload]);

    const handleChange = (e) => {
        const uploadedFile = e.target.files[0];
        if (uploadedFile) {
            setFile(uploadedFile);
            onUpload(uploadedFile);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full"
        >
            <Card
                className={`relative p-12 flex flex-col items-center justify-center border-2 border-dashed transition-all duration-300 glass-card cursor-pointer ${isDragOver ? 'border-primary bg-primary/10' : 'border-white/10 hover:border-white/20'
                    }`}
                onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
                onDragLeave={() => setIsDragOver(false)}
                onDrop={handleDrop}
            >
                <input
                    type="file"
                    id="file-upload"
                    className="absolute inset-0 opacity-0 cursor-pointer"
                    accept={accept}
                    onChange={handleChange}
                />
                <div className="flex flex-col items-center pointer-events-none">
                    {file ? (
                        <CheckCircle2 className="w-16 h-16 text-green-400 mb-4 animate-in zoom-in duration-300" />
                    ) : (
                        <div className="bg-primary/10 p-4 rounded-full mb-4">
                            <Upload className="w-12 h-12 text-primary" />
                        </div>
                    )}
                    <h3 className="text-2xl font-bold mb-2 tracking-tight">
                        {file ? file.name : label}
                    </h3>
                    <p className="text-muted-foreground text-sm">
                        {file ? 'File analysis complete' : 'Drag and drop or click to browse'}
                    </p>
                    {!file && (
                        <div className="mt-6 flex gap-2">
                            <span className="px-2 py-1 bg-white/5 rounded text-[10px] uppercase font-bold text-white/40">DOCX</span>
                            <span className="px-2 py-1 bg-white/5 rounded text-[10px] uppercase font-bold text-white/40">TEMPLATE</span>
                        </div>
                    )}
                </div>
            </Card>
        </motion.div>
    );
}
