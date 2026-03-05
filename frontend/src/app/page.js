"use client";

import React, { useState } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings, RefreshCcw, Send, Activity, Shield, Cpu, Network, FileText, Loader2, CheckCircle, X, PieChart, Info } from 'lucide-react';
import DynamicSlot from '@/components/DynamicSlot';
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// API base URL — resolved at build time via next.config.mjs env injection.
// In Electron packaged mode: FastAPI serves both frontend & API on port 8000
// so relative paths (/api/...) would also work, but explicit base is clearer.
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useToast } from "@/hooks/use-toast";

export default function Home() {
  const [isBulkLoading, setIsBulkLoading] = useState(false);
  const [bulkProgressText, setBulkProgressText] = useState(""); 
  const [template, setTemplate] = useState(null);
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0); 
  const [fileName, setFileName] = useState(""); 
  const [showNamingGuide, setShowNamingGuide] = useState(false);
  const [activeTab, setActiveTab] = useState("all");
  const { toast } = useToast();

  const totalSlots = slots.length;
  const filledSlots = slots.filter(s => {
    if (s.type === 'status') {
      return s.value && String(s.value).trim() !== '';
    }
    return (s.value && String(s.value).trim() !== '') || s.image_base64;
  }).length;

  const completionPercent = totalSlots > 0 ? Math.min(Math.round((filledSlots / totalSlots) * 100), 100) : 0;
  
  const statusOrder = [
    { key: "0_0", label: "Cisco C1300 SW Internet zone" },
    { key: "0_1", label: "Cisco Leaf SW Intranet zone" },
    { key: "1_0", label: "F5 Load Balance Internet zone" },
    { key: "1_1", label: "F5 Load Balance Intranet zone" },
    { key: "2_0", label: "Firewall Palo Alto Internet zone" },
    { key: "2_1", label: "Firewall Palo Alto Intranet zone" }
  ];

  const sections = [
    { id: 'cisco_c1300', title: 'Cisco C1300 Switch', icon: <Network className="w-5 h-5 text-blue-500" /> },
    { id: 'cisco_leaf', title: 'Cisco Leaf Switch', icon: <Network className="w-5 h-5 text-cyan-500" /> },
    { id: 'f5', title: 'F5 Load Balance', icon: <Cpu className="w-5 h-5 text-red-500" /> },
    { id: 'pa', title: 'Firewall Palo Alto', icon: <Shield className="w-5 h-5 text-orange-500" /> },
  ];

  const injectStatusSlots = (originalSlots) => {
    const statusSlots = statusOrder.map(item => ({
      id: `status_${item.key}`,
      label: item.label,
      type: 'status',
      value: 'Normal'
    }));
    return [...originalSlots, ...statusSlots];
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setTemplate(file);
    setFileName(file.name);
    setLoading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_BASE}/api/analyze`, formData, {
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        }
      });

      const slotsWithStatus = injectStatusSlots(response.data.required_slots);
      setSlots(slotsWithStatus);
      toast({ title: "File analysis completed.", description: "The system has successfully created the data entry field.", className: "bg-green-600 text-white border-none" });
    } catch (err) {
      toast({ title: "An error occurred.", description: "The file cannot be analyzed.", variant: "destructive" });
      setTemplate(null);
      setFileName("");
    } finally {
      setLoading(false);
    }
  };

  const updateSlot = (id, data) => {
    setSlots(prev => prev.map(s => s.id === id ? { ...s, ...data } : s));
  };

  const getTargetSlotIndex = (fileName, currentSlots) => {
    const name = fileName.toLowerCase();
    const exactName = name.split('.')[0]; 
    
    return currentSlots.findIndex(slot => {
      const label = slot.label.toLowerCase();
      const id = slot.id ? slot.id.toLowerCase() : "";

      if ((exactName === '1' || name.includes('c1300_avg')) && label.includes('c1300') && (label.includes('avg') || label.includes('average'))) return true;
      if ((exactName === '2' || name.includes('c1300_max')) && label.includes('c1300') && (label.includes('max') || label.includes('maximum'))) return true;
      if ((exactName === '3' || name.includes('leaf_avg')) && label.includes('leaf') && (label.includes('avg') || label.includes('average'))) return true;
      if ((exactName === '4' || name.includes('leaf_max')) && label.includes('leaf') && (label.includes('max') || label.includes('maximum'))) return true;
      if ((exactName === '5' || name.includes('f5_inter')) && label.includes('f5') && label.includes('internet')) return true;
      if ((exactName === '6' || name.includes('f5_intra')) && label.includes('f5') && label.includes('intranet')) return true;
      if ((exactName === '7' || name.includes('avg_cpu_mem')) && label.includes('palo') && (label.includes('avg') || label.includes('average')) && label.includes('cpu')) return true;
      if ((exactName === '8' || name.includes('max_cpu_mem')) && label.includes('palo') && (label.includes('max') || label.includes('maximum')) && label.includes('cpu')) return true;
      if ((exactName === '9' || name.includes('palo_inter')) && label.includes('palo') && label.includes('internet') && label.includes('bandwidth')) return true;
      if ((exactName === '10' || name.includes('palo_intra')) && label.includes('palo') && label.includes('intranet') && label.includes('bandwidth')) return true;

      if (id && name.includes(id) && isNaN(exactName)) return true;
      return false;
    });
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const formattedSlots = slots.map(slot => {
        if (slot.id.toLowerCase().includes('f5')) {
          return {
            ...slot,
            cpu_avg: slot.cpu_avg ? `${String(slot.cpu_avg).replace('%', '')}%` : '',
            cpu_max: slot.cpu_max ? `${String(slot.cpu_max).replace('%', '')}%` : '',
            mem_avg: slot.mem_avg ? `${String(slot.mem_avg).replace('%', '')}%` : '',
            mem_max: slot.mem_max ? `${String(slot.mem_max).replace('%', '')}%` : '',
            traffic_avg: slot.traffic_avg ? String(slot.traffic_avg).replace(/mbps|kbps|gbps|mb\/s|kb\/s/i, '').trim() + ' Mbps' : '',
            traffic_max: slot.traffic_max ? String(slot.traffic_max).replace(/mbps|kbps|gbps|mb\/s|kb\/s/i, '').trim() + ' Mbps' : '',
          };
        }
        return slot;
      });

      const formData = new FormData();
      formData.append('file', template);
      const slotsJson = JSON.stringify(formattedSlots);
      const slotsBlob = new Blob([slotsJson], { type: 'application/json' });
      formData.append('slots', slotsBlob, 'slots.json'); 

      const response = await axios.post(`${API_BASE}/api/generate`, formData, {
        responseType: 'blob',
        headers: { 'Content-Type': 'multipart/form-data' } 
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;

      const today = new Date();
      const dd = String(today.getDate()).padStart(2, '0');
      const mm = String(today.getMonth() + 1).padStart(2, '0'); // มกราคมคือ 0
      const yyyy = today.getFullYear();
      const finalFileName = `Network_Report_${dd}${mm}${yyyy}_(08.00-15.00).docx`;

      link.setAttribute('download', finalFileName);

      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast({ title: "Report successfully generated.", description: "The file has been downloaded successfully.", className: "bg-blue-600 text-white border-none" });
    } catch (err) {
      toast({ title: "An error occurred.", description: "The report cannot be generated.", variant: "destructive" });
    } finally {
      setGenerating(false);
    }
  };

  const handleBulkUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;
    
    setIsBulkLoading(true);
    setBulkProgressText(`Preparing ${files.length} images...`);

    const getBase64 = (file) => new Promise((resolve) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
    });

    let successCount = 0;
    let skipCount = 0;
    let processedCount = 0;

    // 🌟 ใช้ Promise.all ควบคู่กับการอัปเดต State ระหว่างทาง
    const uploadPromises = files.map(async (file) => {
        // หา Index ก่อนเริ่ม (ใช้ค่า slots ตัวตั้งต้นตอนเริ่มอัปโหลด)
        const slotIndex = getTargetSlotIndex(file.name, slots);
        
        if (slotIndex === -1) {
            console.warn(`Skipped: ${file.name} (Name didn't match any slot)`);
            skipCount++;
            processedCount++;
            setBulkProgressText(`Processed ${processedCount}/${files.length}...`);
            return; 
        }

        const targetSlot = slots[slotIndex];
        const base64Image = await getBase64(file);

        try {
            const formData = new FormData();
            formData.append('image', file);
            formData.append('keyword', targetSlot.label);

            const response = await axios.post(`${API_BASE}/api/process-ocr`, formData);
            
            const newData = { ...targetSlot, image_base64: base64Image };
            if (response.data.f5_data) {
                Object.assign(newData, response.data.f5_data);
            } else {
                newData.value = response.data.result;
            }

            // 🌟 ทริคสำคัญ: อัปเดตข้อมูลทันทีที่รูปนี้เสร็จ โดยใช้ prevSlots 
            // ป้องกันข้อมูลหายเวลาที่หลายรูปรันเสร็จพร้อมกัน
            setSlots((prevSlots) => {
                const newSlots = [...prevSlots];
                // หา Index ใหม่จาก prevSlots เผื่อว่าลำดับมีการเปลี่ยนแปลง
                const currentIndex = newSlots.findIndex(s => s.id === targetSlot.id);
                if (currentIndex !== -1) {
                    newSlots[currentIndex] = { ...newSlots[currentIndex], ...newData };
                }
                return newSlots;
            });

            successCount++;
        } catch (error) {
            console.error(`Error OCR ${file.name}:`, error);
            skipCount++;
        } finally {
            processedCount++;
            setBulkProgressText(`Processed ${processedCount}/${files.length}...`);
        }
    });

    // รอให้ทุกรูปทำเสร็จ (แต่ UI จะอัปเดตล่วงหน้าไปเรื่อยๆ แล้วจากโค้ดด้านบน)
    await Promise.all(uploadPromises);

    setIsBulkLoading(false);
    setBulkProgressText(""); 
    
    if (successCount > 0) {
        toast({ title: "Bulk Upload Complete", description: `Success: ${successCount}, Skipped: ${skipCount}`, className: "bg-green-600 text-white border-none" });
    } else {
        toast({ title: "No images processed", description: "Please check your filenames.", variant: "destructive" });
    }
    
    e.target.value = null; 
  };

  const resetUpload = () => {
    setTemplate(null);
    setFileName("");
    setSlots([]);
    setUploadProgress(0);
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-900 font-sans antialiased">
      <main className="max-w-6xl mx-auto px-6 py-16">
        
        <header className="mb-16 text-center">
          <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, ease: "easeOut" }}>
            <Badge variant="secondary" className="bg-blue-100 text-blue-700 hover:bg-blue-200 border-none px-4 py-1.5 mb-5 rounded-full font-semibold transition-colors duration-300 shadow-sm">
              Network Automation
            </Badge>
            <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-slate-900 mb-5">
              Report <span className="text-blue-600 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-cyan-500">Generator</span>
            </h1>
            <p className="text-slate-500 text-lg max-w-xl mx-auto leading-relaxed">
              Automated network structure report generation tool.
            </p>
          </motion.div>
        </header>

        {!template ? (
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }}>
            <Card className="max-w-xl mx-auto border-0 shadow-2xl shadow-blue-900/10 bg-white overflow-hidden group hover:-translate-y-1 transition-all duration-500 cursor-pointer rounded-3xl">
              <div className="relative p-1.5 bg-gradient-to-br from-blue-500 via-blue-400 to-cyan-400">
                <div className="bg-white rounded-[1.25rem] p-12 flex flex-col items-center text-center space-y-6 relative overflow-hidden">
                  <div className="absolute inset-0 bg-blue-50/50 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
                  <input type="file" accept=".docx" onChange={handleFileUpload} className="absolute inset-0 w-full h-full opacity-0 z-20 cursor-pointer" />
                  
                  <motion.div 
                    className="w-24 h-24 bg-blue-50 text-blue-600 rounded-[2rem] flex items-center justify-center group-hover:bg-blue-600 group-hover:text-white transition-colors duration-500 shadow-inner group-hover:shadow-blue-500/30 group-hover:shadow-xl relative z-10"
                    whileHover={{ scale: 1.05, rotate: -5 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <FileText className="w-12 h-12 transition-transform duration-500 group-hover:scale-110" />
                  </motion.div>
                  
                  <div className="relative z-10">
                    <h3 className="text-2xl font-bold text-slate-800 mb-2 group-hover:text-blue-600 transition-colors duration-300">Upload document file</h3>
                    <p className="text-slate-400">Drag and drop your .docx file here, or click to select a file.</p>
                  </div>
                </div>
              </div>
              
              {loading && (
                <div className="absolute inset-0 bg-white/95 backdrop-blur-sm z-30 flex flex-col items-center justify-center p-10 rounded-3xl">
                  <Loader2 className="w-14 h-14 text-blue-600 animate-spin mb-6 drop-shadow-md" />
                  <div className="w-full max-w-xs space-y-3">
                    <div className="flex justify-between text-sm font-bold text-blue-600">
                      <span>Analyzing data...</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <div className="h-4 bg-slate-100 rounded-full overflow-hidden shadow-inner p-0.5">
                      <motion.div className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full" initial={{ width: 0 }} animate={{ width: `${uploadProgress}%` }} transition={{ ease: "easeOut" }} />
                    </div>
                  </div>
                </div>
              )}
            </Card>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
            
            <aside className="lg:col-span-4 space-y-6">
              <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}>
                <Card className="p-6 border-0 shadow-xl shadow-slate-200/50 bg-white rounded-3xl">
                  <div className="flex items-center gap-4 mb-6">
                    <div className="w-14 h-14 bg-green-50 text-green-600 rounded-2xl flex items-center justify-center shadow-inner">
                      <CheckCircle className="w-7 h-7" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <h4 className="font-bold text-slate-800 truncate text-lg">{fileName}</h4>
                      <button 
                        onClick={resetUpload} 
                        className="text-sm font-semibold text-red-500 hover:text-red-600 hover:underline transition-colors mt-0.5"
                      >
                        Change file
                      </button>
                    </div>
                  </div>

                  {/* 🌟 Progress Bar */}
                  <div className="space-y-4 pt-5 border-t border-slate-100">
                    <div className="flex justify-between items-end mb-2">
                        <span className="text-sm font-bold text-slate-600">Completion</span>
                        <motion.span 
                          className={`text-4xl font-black transition-colors duration-500 ${
                            completionPercent === 100 ? 'text-green-500 drop-shadow-sm' : 'text-blue-600'
                          }`}
                          animate={{ scale: completionPercent === 100 ? [1, 1.1, 1] : 1 }}
                          transition={{ duration: 0.5 }}
                        >
                          {completionPercent}%
                        </motion.span>
                    </div>

                    <div className="relative h-4 bg-slate-100 rounded-full overflow-hidden shadow-inner ring-1 ring-slate-200/50 p-0.5">
                        <motion.div 
                          className={`h-full rounded-full transition-colors duration-700 relative overflow-hidden ${
                            completionPercent === 100 
                              ? 'bg-gradient-to-r from-green-400 to-green-500' 
                              : 'bg-gradient-to-r from-blue-400 to-blue-600'
                          }`}
                          initial={{ width: 0 }}
                          animate={{ width: `${completionPercent}%` }}
                          transition={{ type: "spring", stiffness: 60, damping: 15 }}
                        >
                          <div className="absolute top-0 left-0 bottom-0 w-full bg-gradient-to-r from-transparent via-white/30 to-transparent -translate-x-full animate-[shimmer_2s_infinite]" />
                        </motion.div>
                    </div>
                    
                    <div className="flex justify-between items-center text-xs">
                        <span className={`transition-colors duration-300 ${completionPercent === 100 ? "text-green-600 font-bold" : "text-slate-400"}`}>
                          {completionPercent === 100 ? "All slots filled! Ready 🎉" : "Please fill required info."}
                        </span>
                        <span className="font-mono bg-slate-100 px-2.5 py-1 rounded-md text-slate-600 font-bold shadow-sm">
                          {filledSlots} / {totalSlots}
                        </span>
                    </div>
                  </div>
                </Card>
              </motion.div>

              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}>
                <Button 
                  onClick={handleGenerate} 
                  disabled={generating} 
                  className={`w-full h-16 rounded-2xl text-lg font-bold shadow-lg transition-all duration-300 group ${
                    completionPercent === 100 
                      ? 'bg-green-600 hover:bg-green-700 hover:shadow-green-500/30 hover:-translate-y-1 active:scale-95 ring-4 ring-transparent hover:ring-green-500/20' 
                      : 'bg-blue-600 hover:bg-blue-700 hover:shadow-blue-500/30 hover:-translate-y-1 active:scale-95'
                  }`}
                >
                  {generating ? <Loader2 className="animate-spin mr-3 w-6 h-6" /> : <Send className="mr-3 w-6 h-6 group-hover:translate-x-1 transition-transform" />} 
                  {generating ? "Generating..." : "Create a report"}
                </Button>
              </motion.div>
            </aside>

            <div className="lg:col-span-8">
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }}>
                <Card className="mb-6 border-2 border-dashed border-blue-300 bg-blue-50/40 hover:bg-blue-50 transition-all duration-300 rounded-3xl relative overflow-hidden group hover:border-blue-400 hover:shadow-md">
                    <div className="p-10 flex flex-col items-center justify-center text-center space-y-4 relative z-10">
                        <input 
                            type="file" 
                            multiple 
                            accept="image/*" 
                            onChange={handleBulkUpload} 
                            disabled={isBulkLoading}
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed z-10" 
                        />
                        {isBulkLoading ? (
                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center">
                                <Loader2 className="w-12 h-12 text-blue-600 animate-spin mb-3" />
                                <h3 className="text-xl font-bold text-blue-800 mb-2">Processing OCR...</h3>
                                <p className="text-sm font-semibold text-blue-700 bg-blue-100 px-4 py-1.5 rounded-full shadow-inner">{bulkProgressText}</p>
                            </motion.div>
                        ) : (
                            <>
                                <motion.div 
                                  className="w-16 h-16 bg-white text-blue-500 rounded-2xl flex items-center justify-center shadow-sm relative z-0 group-hover:scale-110 group-hover:rotate-6 transition-all duration-300"
                                >
                                    <PieChart className="w-8 h-8" />
                                </motion.div>
                                <div className="relative z-0">
                                  <h3 className="text-xl font-bold text-slate-800 mb-2 group-hover:text-blue-700 transition-colors"> Upload All Images</h3>
                                  <p className="text-sm text-slate-500 max-w-md mx-auto leading-relaxed">
                                      Drag & drop multiple images here. <br/> 
                                      Name them correctly (e.g., <span className="font-mono font-bold text-blue-600 bg-blue-100 px-1.5 py-0.5 rounded">1-10</span> or <span className="font-mono font-bold text-blue-600 bg-blue-100 px-1.5 py-0.5 rounded">c1300_avg.png</span>)
                                  </p>
                                </div>
                                
                                <Button 
                                    variant="outline" 
                                    size="sm" 
                                    onClick={(e) => {
                                        e.preventDefault(); 
                                        setShowNamingGuide(true);
                                    }}
                                    className="mt-4 bg-white text-blue-700 border-blue-200 hover:bg-blue-100 hover:text-blue-800 font-bold relative z-20 shadow-sm hover:shadow active:scale-95 transition-all rounded-xl px-6"
                                >
                                    <Info className="w-4 h-4 mr-2" />
                                    View Naming Guide
                                </Button>
                            </>
                        )}
                    </div>
                </Card>
              </motion.div>

              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, delay: 0.3 }}>
                {/* 🌟 2. เปลี่ยนให้ Tabs ผูกกับ State activeTab */}
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                  
                  <TabsList className="grid grid-cols-2 w-full max-w-[400px] mb-8 bg-slate-200/60 p-1.5 rounded-2xl h-14 shadow-inner relative z-0">
                    
                    <TabsTrigger 
                        value="all" 
                        className="relative rounded-xl font-bold text-base transition-all duration-300 z-10 data-[state=active]:text-blue-700 data-[state=active]:bg-transparent data-[state=active]:shadow-none"
                    >
                        {/* 🌟 3. ก้อนแอนิเมชันสำหรับปุ่มซ้าย */}
                        {activeTab === "all" && (
                            <motion.div 
                                layoutId="activeTabIndicator" 
                                className="absolute inset-0 bg-white rounded-xl shadow-md -z-10" 
                                transition={{ type: "spring", stiffness: 300, damping: 25 }} 
                            />
                        )}
                        Device info
                    </TabsTrigger>

                    <TabsTrigger 
                        value="status" 
                        className="relative rounded-xl font-bold text-base transition-all duration-300 z-10 data-[state=active]:text-blue-700 data-[state=active]:bg-transparent data-[state=active]:shadow-none"
                    >
                        {/* 🌟 4. ก้อนแอนิเมชันสำหรับปุ่มขวา */}
                        {activeTab === "status" && (
                            <motion.div 
                                layoutId="activeTabIndicator" 
                                className="absolute inset-0 bg-white rounded-xl shadow-md -z-10" 
                                transition={{ type: "spring", stiffness: 300, damping: 25 }} 
                            />
                        )}
                        System status
                    </TabsTrigger>

                  </TabsList>

                  <ScrollArea className="h-[800px] pr-4">
                    <TabsContent value="all" className="space-y-10 mt-0">
                      {sections.map(section => {
                        const filteredSlots = slots.filter(s => s.type !== 'status' && (s.id.includes(section.id) || s.label.toLowerCase().includes(section.id)));
                        if (filteredSlots.length === 0) return null;

                        return (
                          <motion.section 
                            key={section.id} 
                            className="space-y-4"
                            initial={{ opacity: 0, y: 10 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.4 }}
                          >
                            <div className="flex items-center gap-3 ml-2 mb-2">
                                <div className="p-2.5 bg-white rounded-xl shadow-sm text-blue-600 border border-slate-100">{section.icon}</div>
                                <h3 className="text-xl font-extrabold text-slate-800 uppercase tracking-wide">{section.title}</h3>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                              {filteredSlots.map(s => (
                                <DynamicSlot key={s.id} slot={s} onUpdate={updateSlot} />
                              ))}
                            </div>
                          </motion.section>
                        );
                      })}
                    </TabsContent>

                    <TabsContent value="status" className="mt-0">
                      <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.4 }}>
                        <Card className="p-8 border-0 shadow-xl bg-white rounded-3xl ring-1 ring-slate-100">
                            <div className="mb-8">
                                <h3 className="text-2xl font-black text-slate-900 flex items-center gap-4">
                                    <div className="p-3 bg-green-50 rounded-2xl shadow-inner">
                                        <Activity className="text-green-600 w-7 h-7" />
                                    </div>
                                    <div className="flex flex-col">
                                        <span>Device Status</span>
                                        <span className="text-sm font-medium text-slate-500 uppercase tracking-wider mt-1">
                                            Check the operating status of network devices.
                                        </span>
                                    </div>
                                </h3>
                            </div>
                            <div className="space-y-4">
                              {slots.filter(s => s.type === 'status').map(s => (
                                  <DynamicSlot key={s.id} slot={s} onUpdate={updateSlot} />
                              ))}
                            </div>
                        </Card>
                      </motion.div>
                    </TabsContent>
                  </ScrollArea>
                </Tabs>
              </motion.div>
            </div>

          </div>
        )}

        {/* 🌟 Popup คู่มือการตั้งชื่อไฟล์พร้อม AnimatePresence ทำให้สมูทตอนเปิด/ปิด */}
        <AnimatePresence>
          {showNamingGuide && (
            <motion.div 
                className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-950/40 backdrop-blur-sm"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setShowNamingGuide(false)}
            >
                <motion.div 
                    className="bg-white rounded-3xl shadow-2xl max-w-2xl w-full overflow-hidden flex flex-col max-h-[90vh]"
                    initial={{ opacity: 0, scale: 0.9, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.9, y: 20 }}
                    transition={{ type: "spring", damping: 25, stiffness: 300 }}
                    onClick={(e) => e.stopPropagation()} 
                >
                    <div className="bg-slate-50/80 backdrop-blur border-b border-slate-100 p-5 px-8 flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="p-2.5 bg-blue-100 text-blue-600 rounded-xl shadow-inner">
                                <FileText className="w-6 h-6" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-slate-800">File Naming Guide</h3>
                                <p className="text-xs font-medium text-slate-500 mt-0.5">เลือกตั้งชื่อไฟล์ได้ 2 รูปแบบ เพื่อให้อัปโหลดเข้าช่องอัตโนมัติ</p>
                            </div>
                        </div>
                        <button 
                            onClick={() => setShowNamingGuide(false)}
                            className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors duration-300"
                        >
                            <X className="w-6 h-6" />
                        </button>
                    </div>

                    <div className="p-8 overflow-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b-2 border-slate-100">
                                    <th className="pb-4 font-black text-xs text-slate-400 uppercase tracking-wider w-32">แบบที่ 1: ตัวเลข</th>
                                    <th className="pb-4 font-black text-xs text-slate-400 uppercase tracking-wider w-44">แบบที่ 2: ชื่อเรียก</th>
                                    <th className="pb-4 font-black text-xs text-slate-400 uppercase tracking-wider">อุปกรณ์ที่รองรับ</th>
                                </tr>
                            </thead>
                            <tbody className="text-[13px]">
                                {[
                                  { num: '1.png', name: 'c1300_avg', desc: 'Cisco C1300 (Average)' },
                                  { num: '2.png', name: 'c1300_max', desc: 'Cisco C1300 (Maximum)' },
                                  { num: '3.png', name: 'leaf_avg', desc: 'Cisco Leaf (Average)' },
                                  { num: '4.png', name: 'leaf_max', desc: 'Cisco Leaf (Maximum)' },
                                  { num: '5.png', name: 'f5_inter', desc: 'F5 (Internet Zone)' },
                                  { num: '6.png', name: 'f5_intra', desc: 'F5 (Intranet Zone)' },
                                  { num: '7.png', name: 'avg_cpu_mem', desc: 'Palo Alto (Avg CPU/Mem)' },
                                  { num: '8.png', name: 'max_cpu_mem', desc: 'Palo Alto (Max CPU/Mem)' },
                                  { num: '9.png', name: 'palo_inter', desc: 'Palo Alto (Inter Bandwidth)' },
                                  { num: '10.png', name: 'palo_intra', desc: 'Palo Alto (Intra Bandwidth)' },
                                ].map((item, idx) => (
                                  <tr key={idx} className="border-b border-slate-50 hover:bg-slate-50/80 transition-colors">
                                      <td className="py-3">
                                          <code className="text-blue-700 bg-blue-50/50 px-2.5 py-1 rounded-md font-bold border border-blue-100/50">{item.num}</code>
                                      </td>
                                      <td className="py-3">
                                          <code className="text-purple-700 bg-purple-50/50 px-2.5 py-1 rounded-md font-bold border border-purple-100/50">{item.name}</code>
                                      </td>
                                      <td className="py-3 font-medium text-slate-700">{item.desc}</td>
                                  </tr>
                                ))}
                            </tbody>
                        </table>
                        
                        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="bg-amber-50/50 border border-amber-200/60 rounded-2xl p-5 flex gap-3">
                              <Info className="w-5 h-5 flex-shrink-0 text-amber-500 mt-0.5" />
                              <div className="text-xs text-amber-900 leading-relaxed">
                                  <strong>Advice:</strong> You can use mixed filenames, e.g. <code>1_backup.jpg</code> will use <strong>1</strong>, or <code>palo_inter_v2.png</code> will use <strong>palo_inter</strong>.
                              </div>
                          </div>
                          <div className="bg-blue-50/50 border border-blue-200/60 rounded-2xl p-5 flex gap-3">
                              <CheckCircle className="w-5 h-5 flex-shrink-0 text-blue-500 mt-0.5" />
                              <div className="text-xs text-blue-900 leading-relaxed">
                                  <strong>Supports files:</strong> .png, .jpg, .jpeg and .webp (For faster OCR, recommend size &lt; 5MB per image.)
                              </div>
                          </div>
                        </div>
                    </div>

                    <div className="bg-slate-50/80 backdrop-blur border-t border-slate-100 p-5 px-8 flex justify-end">
                        <Button 
                          onClick={() => setShowNamingGuide(false)} 
                          className="font-bold bg-slate-900 hover:bg-slate-800 text-white rounded-xl px-10 h-11 transition-all active:scale-95 shadow-md hover:shadow-lg"
                        >
                            Done
                        </Button>
                    </div>
                </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

      </main>
    </div>
  );
}