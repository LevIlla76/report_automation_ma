"use client";
import { motion } from 'framer-motion';
import { 
    CheckCircle, XCircle, Network, Cpu, Shield, Activity,
    Image as ImageIcon, CheckCircle2, Loader2, 
    HardDrive, ArrowUpRight, AlertCircle,
    Eye, Upload, X, FileText 
} from 'lucide-react';
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export default function DynamicSlot({ slot, onUpdate }) {
    const [preview, setPreview] = useState(slot.image_base64 || null);
    const [loading, setLoading] = useState(false);
    const [isViewerOpen, setIsViewerOpen] = useState(false); 
    const { toast } = useToast();

    const isF5 = slot.id.toLowerCase().includes("f5");

    useEffect(() => {
        if (slot.image_base64) {
            setPreview(slot.image_base64);
        } else {
            setPreview(null);
        }
    }, [slot.image_base64]);

    const handleFileChange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const getBase64 = (file) => new Promise((resolve) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => resolve(reader.result);
        });

        const base64Image = await getBase64(file);
        setPreview(base64Image); 

        onUpdate(slot.id, { image_base64: base64Image });

        setLoading(true);
        try {
            const formData = new FormData();
            formData.append('image', file);
            formData.append('keyword', slot.label);
            
            const response = await axios.post(`${API_BASE}/api/process-ocr`, formData);
            
            const newData = {}; 
            
            if (response.data.f5_data) {
                Object.assign(newData, response.data.f5_data);
            } else {
                newData.value = response.data.result;
            }
            
            onUpdate(slot.id, newData); 
            toast({ title: "OCR Success!" });
        } catch (error) {
            toast({ title: "An error occurred", variant: "destructive" });
        } finally { 
            setLoading(false); 
        }
    };

    // 🌟 1. โลจิกเช็ค Icon (ย้ายมาตรงนี้เพื่อให้ใช้ได้ทั้ง 2 ส่วน)
    let DeviceIcon = FileText;
    let iconColorClass = "bg-slate-50 text-slate-600";

    const labelLower = (slot.label || "").toLowerCase();
    const idLower = (slot.id || "").toLowerCase();

    if (labelLower.includes('cisco') || idLower.includes('cisco')) {
        DeviceIcon = Network;
        iconColorClass = "bg-blue-50 text-blue-600"; 
    } else if (labelLower.includes('f5') || idLower.includes('f5')) {
        DeviceIcon = Cpu;
        iconColorClass = "bg-red-50 text-red-600"; 
    } else if (labelLower.includes('palo') || idLower.includes('pa')) {
        DeviceIcon = Shield;
        iconColorClass = "bg-orange-50 text-orange-600"; 
    } else if (slot.type === 'status') {
        DeviceIcon = Activity;
    }

    // --- ส่วนแสดงผล "สถานะระบบ" (System Status) ---
    if (slot.type === 'status') {
        const isNormal = slot.value === 'Normal';
        const isAbnormal = slot.value === 'Abnormal';

        return (
            <div className="flex flex-col gap-3 p-4 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow">
                
                {/* 🌟 แสดงผล Icon ของ Status */}
                <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-xl shadow-inner ${iconColorClass}`}>
                        <DeviceIcon className="w-5 h-5" />
                    </div>
                    <span className="font-bold text-slate-700 text-sm md:text-base">{slot.label}</span>
                </div>
                
                <div className="grid grid-cols-2 gap-2 relative p-1.5 bg-slate-100/80 rounded-xl z-0 mt-1">
                    <button
                        onClick={() => onUpdate(slot.id, { value: 'Normal' })}
                        className={`relative py-2.5 flex items-center justify-center gap-2 rounded-lg font-bold text-sm z-10 transition-colors duration-300 ${
                        isNormal ? 'text-green-700' : 'text-slate-500 hover:text-slate-700'
                        }`}
                    >
                        {isNormal && (
                        <motion.div 
                            layoutId={`status-indicator-${slot.id}`} 
                            className="absolute inset-0 bg-white shadow-sm border border-green-200 rounded-lg -z-10" 
                            transition={{ type: 'spring', stiffness: 350, damping: 25 }} 
                        />
                        )}
                        <CheckCircle className={`w-4 h-4 ${isNormal ? 'text-green-600' : 'text-slate-400'}`} /> 
                        Normal
                    </button>
                    
                    <button
                        onClick={() => onUpdate(slot.id, { value: 'Abnormal' })}
                        className={`relative py-2.5 flex items-center justify-center gap-2 rounded-lg font-bold text-sm z-10 transition-colors duration-300 ${
                        isAbnormal ? 'text-red-700' : 'text-slate-500 hover:text-slate-700'
                        }`}
                    >
                        {isAbnormal && (
                        <motion.div 
                            layoutId={`status-indicator-${slot.id}`} 
                            className="absolute inset-0 bg-white shadow-sm border border-red-200 rounded-lg -z-10" 
                            transition={{ type: 'spring', stiffness: 350, damping: 25 }} 
                        />
                        )}
                        <XCircle className={`w-4 h-4 ${isAbnormal ? 'text-red-600' : 'text-slate-400'}`} /> 
                        Abnormal
                    </button>
                </div>
            </div>
        );
    }

    // --- ส่วนแสดงผล "ข้อมูลอุปกรณ์" (Device Info) ---
    return (
        <>
            <Card className={`bg-white border-slate-200 shadow-sm hover:shadow-md transition-all ${isF5 ? 'md:col-span-2' : ''}`}>
                <CardContent className="p-5 space-y-5">
                    
                    {/* 🌟 2. เปลี่ยน Header ด้านบนสุดให้มี Icon เหมือนกับ Status */}
                    <div className="flex justify-between items-center border-b border-slate-100 pb-3">
                        <div className="flex items-center gap-2.5">
                            <div className={`p-1.5 rounded-lg shadow-inner ${iconColorClass}`}>
                                <DeviceIcon className="w-4 h-4" />
                            </div>
                            <span className="text-sm font-black text-slate-800 uppercase tracking-widest">{slot.label}</span>
                        </div>
                        
                        {(slot.value || slot.cpu_avg) && (
                            <Badge className="bg-green-50 text-green-700 border-green-200 flex gap-1 items-center px-2 py-0">
                                <CheckCircle2 className="w-3 h-3" />
                                <span className="text-[9px]">DATA READY</span>
                            </Badge>
                        )}
                    </div>

                    <div className="space-y-4">
                        {/* ส่วนอัปโหลดรูปภาพ */}
                        <div className="relative h-44 bg-slate-50 rounded-xl border-2 border-dashed border-slate-200 flex items-center justify-center overflow-hidden hover:bg-blue-50/30 hover:border-blue-300 transition-all group">
                            {loading ? (
                                <div className="flex flex-col items-center gap-2">
                                    <Loader2 className="animate-spin text-blue-600 w-8 h-8" />
                                    <span className="text-xs font-bold text-slate-600">Processing</span>
                                </div>
                            ) : preview ? (
                                <div className="relative w-full h-full group/image">
                                    <img src={preview} className="w-full h-full object-contain p-2" alt="Preview" />
                                    <div className="absolute inset-0 bg-slate-900/60 opacity-0 group-hover/image:opacity-100 transition-opacity flex items-center justify-center gap-3 z-20">
                                        <Button size="sm" variant="secondary" onClick={() => setIsViewerOpen(true)} className="h-8 font-bold text-xs bg-white/90 hover:bg-white text-slate-900">
                                            <Eye className="w-4 h-4 mr-1.5 text-blue-600" /> View
                                        </Button>
                                        <div className="relative">
                                            <Button size="sm" variant="secondary" className="h-8 font-bold text-xs bg-white/90 hover:bg-white text-slate-900">
                                                <Upload className="w-4 h-4 mr-1.5 text-blue-600" /> Replace
                                            </Button>
                                            <input type="file" onChange={handleFileChange} className="absolute inset-0 opacity-0 cursor-pointer" />
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <>
                                    <input type="file" onChange={handleFileChange} className="absolute inset-0 opacity-0 cursor-pointer z-10" />
                                    <div className="flex flex-col items-center gap-2 text-slate-400 group-hover:text-blue-500 transition-colors">
                                        <ImageIcon className="w-8 h-8" />
                                        <span className="text-[11px] font-bold uppercase tracking-tighter">Click or drag to upload an image.</span>
                                    </div>
                                </>
                            )}
                        </div>

                        {/* F5 Specific Grid */}
                        {isF5 && (
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
                                <MetricGroup icon={<Cpu className="w-3.5 h-3.5" />} label="CPU Usage" color="blue" unit="%" avgValue={slot.cpu_avg} maxValue={slot.cpu_max} onAvg={(v) => onUpdate(slot.id, {cpu_avg: v})} onMax={(v) => onUpdate(slot.id, {cpu_max: v})} />
                                <MetricGroup icon={<HardDrive className="w-3.5 h-3.5" />} label="Memory" color="purple" unit="%" avgValue={slot.mem_avg} maxValue={slot.mem_max} onAvg={(v) => onUpdate(slot.id, {mem_avg: v})} onMax={(v) => onUpdate(slot.id, {mem_max: v})} />
                                <MetricGroup icon={<ArrowUpRight className="w-3.5 h-3.5" />} label="Traffic Used" color="emerald" unit="Mbps" avgValue={slot.traffic_avg} maxValue={slot.traffic_max} onAvg={(v) => onUpdate(slot.id, {traffic_avg: v})} onMax={(v) => onUpdate(slot.id, {traffic_max: v})} />
                            </div>
                        )}

                        {/* ผลลัพธ์สำหรับอุปกรณ์อื่นๆ */}
                        {!isF5 && (
                            <div className="pt-2">
                                <label className="text-[10px] font-black text-slate-500 uppercase ml-1 flex items-center gap-1 mb-1.5">
                                    <AlertCircle className="w-3 h-3" /> Results detected.
                                </label>
                                <Input 
                                    value={slot.value || ''} 
                                    onChange={(e) => onUpdate(slot.id, {value: e.target.value})} 
                                    className="h-11 bg-white border-slate-300 text-slate-950 font-bold focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all text-sm" 
                                    placeholder="Enter the data value here...." 
                                />
                            </div>
                        )}
                    </div>
                </CardContent>
            </Card>

            {/* ส่วนของ Lightbox (รูปภาพขยายเต็มจอ) */}
            {isViewerOpen && preview && (
                <div 
                    className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 md:p-10 animate-in fade-in duration-200" 
                    onClick={() => setIsViewerOpen(false)} 
                >
                    <button 
                        onClick={() => setIsViewerOpen(false)}
                        className="absolute top-4 right-4 md:top-6 md:right-6 p-2 bg-white/10 hover:bg-white/20 text-white rounded-full backdrop-blur-md transition-all"
                    >
                        <X className="w-6 h-6" />
                    </button>
                    
                    <div 
                        className="relative max-w-full max-h-full bg-white rounded-xl shadow-2xl overflow-hidden flex flex-col"
                        onClick={(e) => e.stopPropagation()} 
                    >
                        <div className="bg-slate-50 border-b border-slate-100 p-3 px-5 flex items-center justify-between">
                            <span className="font-bold text-slate-700 text-sm flex items-center gap-2">
                                <ImageIcon className="w-4 h-4 text-blue-500" />
                                {slot.label}
                            </span>
                        </div>
                        <div className="p-2 overflow-auto flex-1 flex items-center justify-center">
                            <img src={preview} className="max-w-full max-h-[80vh] object-contain rounded" alt="Full Preview" />
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}

function MetricGroup({ icon, label, color, unit, avgValue, maxValue, onAvg, onMax }) {
    const colorClasses = {
        blue: "text-blue-600 bg-blue-50",
        purple: "text-purple-600 bg-purple-50",
        emerald: "text-emerald-600 bg-emerald-50"
    };

    return (
        <div className="space-y-3">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-1.5">
                <div className={`p-1 rounded-md ${colorClasses[color]}`}>
                    {icon}
                </div>
                <span className="text-[11px] font-black text-slate-800 uppercase tracking-tighter">{label}</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
                <MetricInput label="AVG" value={avgValue} onChange={onAvg} unit={unit} />
                <MetricInput label="MAX" value={maxValue} onChange={onMax} unit={unit} />
            </div>
        </div>
    );
}

function MetricInput({ label, value, onChange, unit }) {
    return (
        <div className="space-y-1">
            <span className="text-[9px] font-bold text-slate-500 uppercase ml-1.5">{label}</span>
            <div className="relative flex items-center">
                <Input 
                    value={value || ''} 
                    onChange={(e) => onChange(e.target.value)}
                    className="h-10 text-[13px] font-black text-slate-950 bg-white border-slate-300 focus:bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all shadow-sm pr-10"
                    placeholder="0.00"
                />
                {unit && (
                    <span className="absolute right-3 text-[11px] font-bold text-slate-400 pointer-events-none select-none">
                        {unit}
                    </span>
                )}
            </div>
        </div>
    );
}