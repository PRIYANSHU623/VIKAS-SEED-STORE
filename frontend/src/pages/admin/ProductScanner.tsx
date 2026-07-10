import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Upload, Cpu, ShieldCheck, Loader2, Sparkles, 
  Camera, Trash2, AlertTriangle, Info, Check, X, Plus, Tag, 
  Layers, FileText, AlertCircle, Database, RefreshCw
} from "lucide-react";
import { createProduct, updateProduct } from "../../api/productApi";
import { analyzeProduct } from "../../api/scannerApi";


interface FieldInfo {
  value: any;
  confidence: number;
  source: string;
}

interface OnboardingResult {
  fields: Record<string, FieldInfo>;
  agricultural_metadata: Record<string, string | null>;
  warnings: string[];
  duplicate_info: {
    duplicate_found: boolean;
    message?: string;
    existing_product: {
      id: number;
      name: string;
      brand: string;
      category: string;
      price: number;
      stock: number;
      net_quantity: string;
    } | null;
  };
  tags: string[];
  image_urls: string[];
  web_image_urls: string[];
  timeline: Array<{ step: string; detail: string; timestamp: number; status: string }>;
  confidence: number;
}

export default function ProductScanner() {
  const navigate = useNavigate();
  
  // Dynamic images state (1 to 6 files)
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [activeStepIdx, setActiveStepIdx] = useState(0);
  const [onboardingData, setOnboardingData] = useState<OnboardingResult | null>(null);
  const [selectedThumbnail, setSelectedThumbnail] = useState<string>("");
  
  // Form states during review
  const [activeTab, setActiveTab] = useState<"core" | "specs" | "usage" | "metadata">("core");
  const [newTagInput, setNewTagInput] = useState("");
  const [stockToOnboard, setStockToOnboard] = useState(50);
  
  // Duplicate Resolution State
  const [ignoreDuplicateWarning, setIgnoreDuplicateWarning] = useState(false);
  const [updatingStock, setUpdatingStock] = useState(false);
  const [stockToAdd, setStockToAdd] = useState(50);
  const [updateStockSuccess, setUpdateStockSuccess] = useState(false);

  // Camera capture states
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [availableDevices, setAvailableDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>("");
  const [cameraError, setCameraError] = useState<string>("");
  const videoRef = useRef<HTMLVideoElement>(null);

  // Bind camera stream to video tag
  useEffect(() => {
    if (videoRef.current && cameraStream) {
      videoRef.current.srcObject = cameraStream;
    }
  }, [cameraStream]);

  // Hardcoded workflow steps for smooth frontend loading animations
  const onboardingSteps = [
    { name: "Uploading Images", desc: "Saving assets to backend storage..." },
    { name: "Analyzing Images", desc: "Running multi-angle vision models..." },
    { name: "Extracting Product Information", desc: "Parsing packaging text & labels..." },
    { name: "Validating Data", desc: "Checking compliance and format rules..." },
    { name: "Searching Trusted Sources", desc: "Querying manufacturer database/brochures..." },
    { name: "Detecting Duplicates", desc: "Searching catalog for existing products..." },
    { name: "Generating Metadata", desc: "Inferring soil, season and dosage rules..." },
    { name: "Preparing Review", desc: "Formulating confidence details..." },
    { name: "Ready for Approval", desc: "Onboarding details ready for admin review." }
  ];

  // Camera Controls
  const startCamera = async (deviceId?: string) => {
    setCameraActive(true);
    setCameraError("");
    try {
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
      }

      const constraints: MediaStreamConstraints = {
        video: deviceId ? { deviceId: { exact: deviceId } } : { facingMode: "environment" }
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      setCameraStream(stream);

      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(device => device.kind === "videoinput");
      setAvailableDevices(videoDevices);
      
      if (videoDevices.length > 0 && !deviceId) {
        const activeTrack = stream.getVideoTracks()[0];
        const activeSettings = activeTrack ? activeTrack.getSettings() : null;
        if (activeSettings && activeSettings.deviceId) {
          setSelectedDeviceId(activeSettings.deviceId);
        } else {
          setSelectedDeviceId(videoDevices[0].deviceId);
        }
      }
    } catch (err: any) {
      console.error("Camera access error:", err);
      setCameraError("Could not access camera. Please verify permissions or upload files directly.");
    }
  };

  const stopCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop());
      setCameraStream(null);
    }
    setCameraActive(false);
    setAvailableDevices([]);
    setSelectedDeviceId("");
    setCameraError("");
  };

  const capturePhoto = () => {
    if (!cameraStream || !videoRef.current) return;

    const video = videoRef.current;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;

    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => {
        if (blob) {
          const file = new File([blob], `captured_image_${Date.now()}.jpg`, { type: "image/jpeg" });
          if (uploadedFiles.length >= 6) {
            alert("A maximum of 6 images is allowed.");
            return;
          }
          setUploadedFiles(prev => [...prev, file]);
          stopCamera();
        }
      }, "image/jpeg", 0.92);
    }
  };

  const removeFile = (idx: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== idx));
  };

  // Pipeline Execution
  const handleAnalyze = async () => {
    if (uploadedFiles.length < 1) {
      alert("Please upload or capture at least 1 product image.");
      return;
    }
    if (uploadedFiles.length > 6) {
      alert("A maximum of 6 images can be analyzed.");
      return;
    }

    try {
      setLoading(true);
      setOnboardingData(null);
      setIgnoreDuplicateWarning(false);
      setUpdateStockSuccess(false);

      // Setup stepping animations for premium UI response
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 95) {
            clearInterval(interval);
            return 95;
          }
          return prev + 1;
        });
      }, 150);

      // Fake stepper message index tracker
      const stepTimer = setInterval(() => {
        setActiveStepIdx(prev => {
          if (prev >= onboardingSteps.length - 2) {
            clearInterval(stepTimer);
            return onboardingSteps.length - 2;
          }
          return prev + 1;
        });
      }, 1800);

      const formData = new FormData();
      uploadedFiles.forEach((file) => {
        formData.append("images", file);
      });

      const result = await analyzeProduct(formData);
      
      // Perform local storage duplicate check if backend check did not find one
      if (!result.duplicate_info?.duplicate_found) {
        const local = localStorage.getItem("products");
        const nameInput = result.fields.name.value || "";
        const brandInput = result.fields.brand.value || "";
        const weightInput = result.fields.weight.value || result.fields.net_quantity.value || "";
        
        if (local && nameInput) {
          const products = JSON.parse(local);
          const cleanNameInput = nameInput.toLowerCase().replace(/[\s\-_,\.]/g, "");
          const cleanBrandInput = brandInput.toLowerCase().replace(/[\s\-_,\.]/g, "");
          const cleanWeightInput = weightInput.toLowerCase().replace(/[\s\-_,\.]/g, "");
          
          const found = products.find((p: any) => {
            const pName = p.name.toLowerCase().replace(/[\s\-_,\.]/g, "");
            const pBrand = (p.brand || "").toLowerCase().replace(/[\s\-_,\.]/g, "");
            const pWeight = (p.net_quantity || p.weight || "").toLowerCase().replace(/[\s\-_,\.]/g, "");
            
            const nameMatch = (cleanNameInput.includes(pName) || pName.includes(cleanNameInput));
            const brandMatch = (cleanBrandInput === pBrand || !cleanBrandInput || !pBrand);
            const weightMatch = (cleanWeightInput === pWeight || !cleanWeightInput || !pWeight);
            
            return nameMatch && brandMatch && weightMatch;
          });
          
          if (found) {
            result.duplicate_info = {
              duplicate_found: true,
              message: "This product already exists in local catalog.",
              existing_product: {
                id: found.id,
                name: found.name,
                brand: found.brand,
                category: found.category,
                price: found.price,
                stock: found.stock,
                net_quantity: found.net_quantity || found.weight || weightInput
              }
            };
          }
        }
      }

      clearInterval(interval);
      clearInterval(stepTimer);
      setProgress(100);
      setActiveStepIdx(onboardingSteps.length - 1);
      
      // Load response into state
      setOnboardingData(result);
      if (result.image_urls && result.image_urls.length > 0) {
        setSelectedThumbnail(result.image_urls[0]);
      } else if (result.web_image_urls && result.web_image_urls.length > 0) {
        setSelectedThumbnail(result.web_image_urls[0]);
      }
    } catch (err: any) {
      console.error(err);
      alert(
        err.response?.data?.detail || "Product onboarding failed. Please ensure the backend is running and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  // Field Edit Handlers
  const handleFieldChange = (fieldName: string, newValue: any) => {
    if (!onboardingData) return;
    setOnboardingData({
      ...onboardingData,
      fields: {
        ...onboardingData.fields,
        [fieldName]: {
          ...onboardingData.fields[fieldName],
          value: newValue,
          confidence: 100, // modified fields updated to admin absolute confidence
          source: "Administrator Edit"
        }
      }
    });
  };

  const handleMetadataChange = (key: string, newValue: any) => {
    if (!onboardingData) return;
    setOnboardingData({
      ...onboardingData,
      agricultural_metadata: {
        ...onboardingData.agricultural_metadata,
        [key]: newValue
      }
    });
  };

  // Tag Management
  const addTag = () => {
    if (!onboardingData || !newTagInput.trim()) return;
    if (onboardingData.tags.includes(newTagInput.trim())) {
      setNewTagInput("");
      return;
    }
    setOnboardingData({
      ...onboardingData,
      tags: [...onboardingData.tags, newTagInput.trim()]
    });
    setNewTagInput("");
  };

  const removeTag = (tagToRemove: string) => {
    if (!onboardingData) return;
    setOnboardingData({
      ...onboardingData,
      tags: onboardingData.tags.filter(t => t !== tagToRemove)
    });
  };

  // Save Approved Product
  const handleApproveAndSave = async () => {
    if (!onboardingData) return;

    setLoading(true);

    // Convert local scanned image to base64 if selected
    let finalImageUrl = selectedThumbnail || "";
    if (finalImageUrl.startsWith("/uploads/")) {
      try {
        // Match the index from the filename, e.g. /uploads/products/123_abc_2.jpg
        const match = finalImageUrl.match(/_(\d+)\.[^.]+$/);
        if (match) {
          const fileIdx = parseInt(match[1], 10);
          const file = uploadedFiles[fileIdx];
          if (file) {
            finalImageUrl = await new Promise<string>((resolve, reject) => {
              const reader = new FileReader();
              reader.onload = () => resolve(reader.result as string);
              reader.onerror = (error) => reject(error);
              reader.readAsDataURL(file);
            });
          }
        }
      } catch (err) {
        console.error("Failed to convert selected thumbnail to base64:", err);
      }
    }

    const payload = {
      name: onboardingData.fields.name.value,
      brand: onboardingData.fields.brand.value,
      category: onboardingData.fields.category.value || "seeds",
      description: onboardingData.fields.description.value,
      price: onboardingData.fields.mrp.value || 0.0,
      stock: stockToOnboard,
      image_url: finalImageUrl,
      kind: onboardingData.fields.category.value === "seeds" ? onboardingData.fields.seed_kind.value : null,
      season: onboardingData.fields.category.value === "seeds" ? onboardingData.fields.recommended_season.value : null,
      
      // Add new onboarding specifics
      manufacturer: onboardingData.fields.manufacturer.value,
      net_quantity: onboardingData.fields.net_quantity.value || onboardingData.fields.weight.value,
      batch_number: onboardingData.fields.batch_number.value,
      mfg_date: onboardingData.fields.manufacturing_date.value,
      expiry_date: onboardingData.fields.expiry_date.value,
      registration_number: onboardingData.fields.registration_number.value,
      ingredients: onboardingData.fields.ingredients.value,
      chemical_composition: onboardingData.fields.chemical_composition.value,
      usage_instructions: onboardingData.fields.usage_instructions.value,
      storage_instructions: onboardingData.fields.storage_instructions.value,
      safety_warnings: onboardingData.fields.safety_warnings.value,
      license_numbers: onboardingData.fields.license_numbers.value,
      
      // Save tags, metadata, scores and sources
      agricultural_metadata: onboardingData.agricultural_metadata,
      confidence_scores: Object.keys(onboardingData.fields).reduce((acc, key) => {
        acc[key] = onboardingData.fields[key].confidence;
        return acc;
      }, {} as Record<string, number>),
      sources: Object.keys(onboardingData.fields).reduce((acc, key) => {
        acc[key] = onboardingData.fields[key].source;
        return acc;
      }, {} as Record<string, string>),
      tags: onboardingData.tags
    };

    try {
      await createProduct(payload);
      alert(`Successfully onboarded and published ${payload.name}!`);
    } catch (err: any) {
      console.warn("Failed to onboard product to backend, saving in local storage as fallback:", err);
      
      // Safe fallback: save directly to local storage cache
      const local = localStorage.getItem("products");
      const products = local ? JSON.parse(local) : [];
      const newLocalProduct = {
        ...payload,
        id: `prod-${Date.now()}`,
        image: payload.image_url || "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&q=80&w=600",
        rating: 5.0,
        reviewsCount: 0
      };
      
      // Remove duplicate by name if exists in local list before inserting
      const filtered = products.filter((p: any) => p.name.toLowerCase() !== newLocalProduct.name.toLowerCase());
      filtered.unshift(newLocalProduct);
      localStorage.setItem("products", JSON.stringify(filtered));
      
      alert(`Onboarded ${payload.name} locally (Offline mode active).`);
    } finally {
      setLoading(false);
      navigate("/admin");
    }
  };

  // Update existing stock
  const handleUpdateStock = async () => {
    if (!onboardingData?.duplicate_info.existing_product) return;
    
    setUpdatingStock(true);
    const prod = onboardingData.duplicate_info.existing_product;
    const finalStock = prod.stock + (Number(stockToAdd) || 0);

    try {
      await updateProduct(prod.id, {
        stock: finalStock
      });
      
      // Update local storage directly to keep in sync
      const local = localStorage.getItem("products");
      if (local) {
        const products = JSON.parse(local);
        const index = products.findIndex((p: any) => p.id.toString() === prod.id.toString() || p.name.toLowerCase() === prod.name.toLowerCase());
        if (index !== -1) {
          products[index].stock = finalStock;
          localStorage.setItem("products", JSON.stringify(products));
        }
      }

      setUpdateStockSuccess(true);
      alert(`Updated stock for ${prod.name} successfully! Current Stock: {${finalStock}}`);
      setTimeout(() => {
        navigate("/admin");
      }, 1500);
    } catch (err) {
      console.warn("Failed to update stock on backend database, updating local cache:", err);
      
      // Update local storage direct fallback
      const local = localStorage.getItem("products");
      if (local) {
        const products = JSON.parse(local);
        const index = products.findIndex((p: any) => p.id.toString() === prod.id.toString() || p.name.toLowerCase() === prod.name.toLowerCase());
        if (index !== -1) {
          products[index].stock = finalStock;
          localStorage.setItem("products", JSON.stringify(products));
        }
      }
      
      setUpdateStockSuccess(true);
      alert(`Updated stock for ${prod.name} locally! Current Stock: ${finalStock}`);
      setTimeout(() => {
        navigate("/admin");
      }, 1500);
    } finally {
      setUpdatingStock(false);
    }
  };

  return (
    <div className="space-y-8 pb-16 max-w-6xl mx-auto px-4 md:px-0">
      
      {/* Premium Header */}
      <div className="bg-gradient-to-r from-emerald-950 via-teal-900 to-emerald-900 text-white rounded-3xl p-8 shadow-2xl relative overflow-hidden">
        {/* Glow effect */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-teal-400 rounded-full filter blur-[100px] opacity-20 pointer-events-none"></div>
        <div className="relative z-10 space-y-3">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-teal-400/10 text-teal-300 text-xs font-extrabold rounded-full border border-teal-400/20 tracking-wider uppercase">
            <Cpu size={13} className="animate-pulse" /> Advanced AI Onboarding Agent
          </span>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight">
            AI Product Onboarding Agent
          </h1>
          <p className="text-teal-100 max-w-2xl text-sm leading-relaxed">
            Upload up to 6 high-resolution product photos. The agent utilizes Gemini Vision to automatically extract fields, performs internet search validation, verifies postgres duplicates, and builds agricultural metadata catalogs.
          </p>
        </div>
      </div>

      {!onboardingData && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Upload panel (Left) */}
          <div className="lg:col-span-7 space-y-6">
            <div className="bg-white border border-gray-100 rounded-3xl p-6 shadow-xl space-y-6">
              <div>
                <h3 className="font-extrabold text-gray-900 text-base">
                  Upload Product Packaging Images
                </h3>
                <p className="text-gray-400 text-xs mt-1">
                  Provide 1 to 6 packaging pictures (e.g., Front label, ingredients panel, storage guidelines, batch stamps).
                </p>
              </div>

              {/* Dynamic Image Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {uploadedFiles.map((file, idx) => (
                  <div key={idx} className="relative group aspect-square rounded-2xl overflow-hidden border border-teal-100 bg-teal-50/20 flex flex-col items-center justify-center">
                    <img 
                      src={URL.createObjectURL(file)} 
                      alt={`Product Angle ${idx + 1}`} 
                      className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                    />
                    {/* Floating remove button */}
                    <button
                      onClick={() => removeFile(idx)}
                      className="absolute top-2 right-2 p-1.5 bg-red-600/90 text-white rounded-full hover:bg-red-700 transition shadow"
                    >
                      <Trash2 size={13} />
                    </button>
                    <span className="absolute bottom-2 left-2 px-2 py-0.5 bg-black/60 text-white text-[9px] font-bold rounded">
                      Angle #{idx + 1}
                    </span>
                  </div>
                ))}

                {/* Empty Upload Slots if < 6 */}
                {uploadedFiles.length < 6 && (
                  <label className="border-2 border-dashed border-gray-200 hover:border-teal-500 rounded-2xl aspect-square flex flex-col items-center justify-center p-4 cursor-pointer bg-gray-50/50 hover:bg-teal-50/10 transition duration-300">
                    <input 
                      type="file" 
                      multiple 
                      accept="image/*" 
                      className="hidden" 
                      onChange={(e) => {
                        const files = Array.from(e.target.files || []);
                        const total = [...uploadedFiles, ...files];
                        if (total.length > 6) {
                          alert("A maximum of 6 images can be uploaded.");
                          setUploadedFiles(total.slice(0, 6));
                        } else {
                          setUploadedFiles(total);
                        }
                      }}
                    />
                    <Upload size={32} className="text-gray-400 group-hover:text-teal-600" />
                    <span className="text-[11px] font-bold text-gray-700 mt-2 text-center">Add Image File</span>
                    <span className="text-[9px] text-gray-400 text-center mt-1">({uploadedFiles.length}/6 uploaded)</span>
                  </label>
                )}

                {/* Camera Trigger Slot */}
                {uploadedFiles.length < 6 && (
                  <button
                    type="button"
                    onClick={() => startCamera()}
                    className="border-2 border-dashed border-gray-200 hover:border-teal-500 rounded-2xl aspect-square flex flex-col items-center justify-center p-4 bg-gray-50/50 hover:bg-teal-50/10 transition duration-300"
                  >
                    <Camera size={32} className="text-teal-600" />
                    <span className="text-[11px] font-bold text-teal-700 mt-2">Take Live Photo</span>
                    <span className="text-[9px] text-gray-400 mt-1">Direct Capture</span>
                  </button>
                )}
              </div>

              {/* Run Agent trigger button */}
              <button
                onClick={handleAnalyze}
                disabled={loading || uploadedFiles.length === 0}
                className="w-full py-4 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 active:scale-[0.98] disabled:from-gray-200 disabled:to-gray-200 disabled:text-gray-400 text-white font-extrabold rounded-2xl transition shadow-lg flex items-center justify-center gap-2.5 text-sm uppercase tracking-wider"
              >
                {loading ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    Onboarding Agent Executing...
                  </>
                ) : (
                  <>
                    <Sparkles size={18} />
                    Onboard Product with AI
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Guidelines & Quick Guide (Right) */}
          <div className="lg:col-span-5 space-y-6">
            
            {/* Live running step loader */}
            {loading && (
              <div className="bg-white border border-gray-100 rounded-3xl p-6 shadow-xl space-y-6">
                <div className="space-y-2">
                  <div className="flex justify-between items-center text-xs font-bold text-gray-500 uppercase tracking-widest">
                    <span>Onboarding Pipeline Progress</span>
                    <span className="text-teal-600">{progress}%</span>
                  </div>
                  <div className="w-full bg-gray-100 h-2.5 rounded-full overflow-hidden">
                    <div 
                      style={{ width: `${progress}%` }} 
                      className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full transition-all duration-300"
                    />
                  </div>
                </div>

                {/* Vertical Timeline Steps */}
                <div className="space-y-4 pt-2">
                  <span className="text-[10px] font-extrabold uppercase text-gray-400 tracking-wider">
                    Pipeline Stages
                  </span>
                  
                  <div className="relative border-l border-gray-100 pl-6 ml-2 space-y-6">
                    {onboardingSteps.map((step, idx) => {
                      const isActive = idx === activeStepIdx;
                      const isCompleted = idx < activeStepIdx;
                      
                      return (
                        <div key={idx} className="relative">
                          <span className={`absolute -left-8 top-0.5 rounded-full w-4.5 h-4.5 flex items-center justify-center text-[9px] font-bold border transition duration-300 ${
                            isActive 
                              ? "bg-teal-500 text-white border-teal-500 shadow animate-pulse"
                              : isCompleted
                                ? "bg-emerald-100 text-emerald-700 border-emerald-200"
                                : "bg-white text-gray-300 border-gray-200"
                          }`}>
                            {isCompleted ? <Check size={10} strokeWidth={3} /> : idx + 1}
                          </span>
                          <div className={`space-y-0.5 transition duration-300 ${isActive ? "opacity-100" : "opacity-50"}`}>
                            <h4 className={`text-xs font-bold ${isActive ? "text-teal-700" : "text-gray-700"}`}>
                              {step.name}
                            </h4>
                            <p className="text-[10px] text-gray-400 font-medium">{step.desc}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}

            {!loading && (
              <div className="bg-gray-50/50 border border-gray-100 rounded-3xl p-6 space-y-4">
                <h4 className="font-extrabold text-sm text-gray-900 uppercase tracking-wider flex items-center gap-1.5">
                  <Info size={16} className="text-teal-600" /> Scanner instructions
                </h4>
                <ul className="text-xs text-gray-500 space-y-3 list-disc pl-4 leading-relaxed">
                  <li><strong>Multiple Views:</strong> Upload at least 2 angles (front and back/spec panels) for optimum extraction confidence.</li>
                  <li><strong>Avoid Blurs:</strong> Ensure text, barcode, MRP figures, and chemical active percentages are clear in your photos.</li>
                  <li><strong>Enrichment:</strong> Missing or blurry fields trigger programmatic search catalogs across manufacturer pages (e.g. Bayer, Syngenta, IFFCO).</li>
                  <li><strong>Admin approval:</strong> No products are saved automatically. You must inspect the final details and approve.</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Review & Edit Onboarding Results Page */}
      {onboardingData && !loading && (
        <div className="space-y-8 animate-in fade-in zoom-in-98 duration-300">
          
          {/* Timeline & Summary Alert banner */}
          <div className="bg-white border border-teal-100 rounded-3xl p-6 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-widest text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">
                  Ready for Approval
                </span>
                <span className="text-xs font-bold text-teal-600 bg-teal-50 px-2 py-0.5 rounded border border-teal-100">
                  Overall Confidence: {onboardingData.confidence}%
                </span>
              </div>
              <h2 className="text-xl font-extrabold text-gray-900 tracking-tight">
                Review extracted specifications for "{onboardingData.fields.name.value || "New Product"}"
              </h2>
              <p className="text-gray-400 text-xs">
                Inspect details below, edit low-confidence fields (highlighted in red), verify warnings, and select save path.
              </p>
            </div>
            
            <div className="flex gap-3">
              <button 
                onClick={() => setOnboardingData(null)}
                className="px-4 py-2 bg-gray-50 hover:bg-gray-100 text-gray-700 text-xs font-extrabold rounded-xl border border-gray-200 transition"
              >
                Scan Another
              </button>
            </div>
          </div>

          {/* Validation Warnings Card */}
          {onboardingData.warnings.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-3xl p-5 shadow-sm flex items-start gap-4">
              <AlertTriangle className="text-amber-600 shrink-0 mt-0.5" size={20} />
              <div className="space-y-1">
                <h4 className="text-xs font-extrabold text-amber-800 uppercase tracking-widest">
                  Validation Warnings ({onboardingData.warnings.length})
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-1.5 pt-1.5">
                  {onboardingData.warnings.map((w, idx) => (
                    <div key={idx} className="flex items-center gap-1.5 text-xs text-amber-700 font-medium">
                      <span className="w-1.5 h-1.5 bg-amber-500 rounded-full"></span>
                      {w}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Duplicate Detection resolutions panel */}
          {onboardingData.duplicate_info.duplicate_found && !ignoreDuplicateWarning && (
            <div className="bg-red-50 border border-red-200 rounded-3xl p-6 shadow-md space-y-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="text-red-600 shrink-0 mt-1" size={24} />
                <div className="space-y-1">
                  <h3 className="font-extrabold text-sm text-red-900 uppercase tracking-widest">
                    Duplicate Product Warning: This product already exists
                  </h3>
                  <p className="text-xs text-red-700 leading-relaxed">
                    A product named <strong>{onboardingData.duplicate_info.existing_product?.name}</strong> (Brand: {onboardingData.duplicate_info.existing_product?.brand}, Weight: {onboardingData.duplicate_info.existing_product?.net_quantity}) already exists in PostgreSQL database with <strong>{onboardingData.duplicate_info.existing_product?.stock}</strong> in stock.
                  </p>
                </div>
              </div>

              {updateStockSuccess ? (
                <div className="p-3 bg-green-100 border border-green-200 text-green-800 font-bold rounded-xl text-center text-xs">
                  Stock successfully updated! Navigating back...
                </div>
              ) : (
                <div className="bg-white border border-red-100 rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <Database className="text-gray-400" size={20} />
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Update existing stock quantity</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-700">Add to Stock:</span>
                        <input
                          type="number"
                          value={stockToAdd}
                          onChange={(e) => setStockToAdd(Math.max(1, parseInt(e.target.value) || 0))}
                          className="w-20 p-1 border border-gray-200 rounded text-xs text-center focus:outline-none focus:ring-1 focus:ring-red-500"
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex flex-wrap gap-2.5 w-full sm:w-auto">
                    <button
                      onClick={handleUpdateStock}
                      disabled={updatingStock}
                      className="flex-1 sm:flex-none px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white text-xs font-extrabold rounded-xl transition shadow flex items-center justify-center gap-1.5"
                    >
                      {updatingStock ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />}
                      Update Existing Stock
                    </button>
                    <button
                      onClick={() => setIgnoreDuplicateWarning(true)}
                      className="flex-1 sm:flex-none px-4 py-2.5 bg-gray-50 hover:bg-gray-100 text-gray-700 text-xs font-extrabold rounded-xl border border-gray-200 transition"
                    >
                      Create New Product Anyway
                    </button>
                    <button
                      onClick={() => navigate("/admin")}
                      className="flex-1 sm:flex-none px-4 py-2.5 bg-white hover:bg-gray-50 text-gray-500 text-xs font-extrabold rounded-xl border border-gray-200 transition"
                    >
                      Cancel Onboarding
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Two column edit structure */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            
            {/* Left side: Images gallery and edit inputs */}
            <div className="lg:col-span-8 space-y-6">
              
              {/* Image Previews */}
              <div className="bg-white border border-gray-100 rounded-3xl p-5 shadow-lg space-y-3">
                <h4 className="font-extrabold text-xs text-gray-900 uppercase tracking-widest">
                  Uploaded catalog images ({onboardingData.image_urls.length})
                </h4>
                <div className="flex gap-3 overflow-x-auto pb-2">
                  {onboardingData.image_urls.map((url, i) => (
                    <img 
                      key={i}
                      src={`import.meta.env.VITE_API_URL${url}`}
                      alt="Product Spec" 
                      className="h-20 w-28 object-cover rounded-xl border border-gray-100 shadow-sm flex-shrink-0"
                    />
                  ))}
                </div>
              </div>

              {/* Fields Tabs navigation */}
              <div className="bg-white border border-gray-100 rounded-3xl shadow-xl overflow-hidden">
                <div className="flex border-b border-gray-100 bg-gray-50/50 p-2 gap-1.5">
                  {[
                    { id: "core", label: "Core Information" },
                    { id: "specs", label: "Specifications & Dates" },
                    { id: "usage", label: "Usage & Warnings" },
                    { id: "metadata", label: "Agricultural Metadata" }
                  ].map((t) => (
                    <button
                      key={t.id}
                      onClick={() => setActiveTab(t.id as any)}
                      className={`flex-1 py-2 px-3 text-xs font-extrabold rounded-xl transition ${
                        activeTab === t.id 
                          ? "bg-teal-600 text-white shadow"
                          : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
                      }`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>

                {/* Editable Fields Content */}
                <div className="p-6 space-y-5">
                  
                  {/* TAB 1: CORE DETAILS */}
                  {activeTab === "core" && (
                    <div className="space-y-4">
                      {/* Name input */}
                      {renderEditableField("name", "Product Name", onboardingData.fields.name, handleFieldChange)}
                      
                      {/* Brand input */}
                      {renderEditableField("brand", "Brand", onboardingData.fields.brand, handleFieldChange)}

                      {/* Manufacturer input */}
                      {renderEditableField("manufacturer", "Manufacturer", onboardingData.fields.manufacturer, handleFieldChange)}

                      {/* Category select */}
                      <div className="grid grid-cols-1 md:grid-cols-4 items-start gap-4 border-b border-gray-50 pb-4">
                        <div className="md:col-span-1 pt-2">
                          <label className="text-xs font-bold text-gray-700 uppercase tracking-widest">
                            Category
                          </label>
                        </div>
                        <div className="md:col-span-3 space-y-2">
                          <select
                            value={onboardingData.fields.category.value || "seeds"}
                            onChange={(e) => handleFieldChange("category", e.target.value)}
                            className="w-full border border-gray-200 rounded-xl p-3 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
                          >
                            <option value="seeds">Seeds</option>
                            <option value="fertilizers">Fertilizers</option>
                            <option value="herbicides">Herbicides</option>
                            <option value="pesticides">Pesticides</option>
                          </select>
                          {renderFieldMetaBadge(onboardingData.fields.category)}
                        </div>
                      </div>

                      {/* Crop Type input */}
                      {renderEditableField("crop_type", "Crop Type", onboardingData.fields.crop_type, handleFieldChange)}
                    </div>
                  )}

                  {/* TAB 2: SPECS AND DATES */}
                  {activeTab === "specs" && (
                    <div className="space-y-4">
                      {/* Price input */}
                      <div className="grid grid-cols-1 md:grid-cols-4 items-start gap-4 border-b border-gray-50 pb-4">
                        <div className="md:col-span-1 pt-2">
                          <label className="text-xs font-bold text-gray-700 uppercase tracking-widest">
                            MRP Price (₹)
                          </label>
                        </div>
                        <div className="md:col-span-3 space-y-2">
                          <input
                            type="number"
                            value={onboardingData.fields.mrp.value || ""}
                            onChange={(e) => handleFieldChange("mrp", parseFloat(e.target.value) || 0.0)}
                            className={`w-full border rounded-xl p-3 text-xs focus:outline-none focus:ring-2 focus:ring-teal-500 ${
                              onboardingData.fields.mrp.confidence < 80 ? "border-red-300 bg-red-50/20" : "border-gray-200"
                            }`}
                          />
                          {renderFieldMetaBadge(onboardingData.fields.mrp)}
                        </div>
                      </div>

                      {/* Weight input */}
                      {renderEditableField("weight", "Weight/Volume", onboardingData.fields.weight, handleFieldChange)}

                      {/* Net Quantity */}
                      {renderEditableField("net_quantity", "Net Quantity", onboardingData.fields.net_quantity, handleFieldChange)}

                      {/* Batch Number */}
                      {renderEditableField("batch_number", "Batch Number", onboardingData.fields.batch_number, handleFieldChange)}

                      {/* Mfg Date */}
                      {renderEditableField("manufacturing_date", "Manufacturing Date", onboardingData.fields.manufacturing_date, handleFieldChange)}

                      {/* Expiry Date */}
                      {renderEditableField("expiry_date", "Expiry Date", onboardingData.fields.expiry_date, handleFieldChange)}

                      {/* Registration Number */}
                      {renderEditableField("registration_number", "Registration Number", onboardingData.fields.registration_number, handleFieldChange)}
                    </div>
                  )}

                  {/* TAB 3: USAGE & COMPOSITION */}
                  {activeTab === "usage" && (
                    <div className="space-y-4">
                      {/* Ingredients */}
                      {renderEditableField("ingredients", "Ingredients", onboardingData.fields.ingredients, handleFieldChange, "textarea")}

                      {/* Chemical composition */}
                      {renderEditableField("chemical_composition", "Chemical Composition", onboardingData.fields.chemical_composition, handleFieldChange, "textarea")}

                      {/* Usage Instructions */}
                      {renderEditableField("usage_instructions", "Usage Instructions", onboardingData.fields.usage_instructions, handleFieldChange, "textarea")}

                      {/* Storage Instructions */}
                      {renderEditableField("storage_instructions", "Storage Instructions", onboardingData.fields.storage_instructions, handleFieldChange, "textarea")}

                      {/* Safety warnings */}
                      {renderEditableField("safety_warnings", "Safety Warnings", onboardingData.fields.safety_warnings, handleFieldChange, "textarea")}

                      {/* License numbers */}
                      {renderEditableField("license_numbers", "License Numbers", onboardingData.fields.license_numbers, handleFieldChange)}
                    </div>
                  )}

                  {/* TAB 4: METADATA */}
                  {activeTab === "metadata" && (
                    <div className="space-y-4">
                      <div className="p-4 bg-teal-50/30 border border-teal-100 rounded-2xl flex items-start gap-3">
                        <Layers className="text-teal-600 mt-0.5 shrink-0" size={16} />
                        <div className="space-y-0.5 text-xs text-teal-800">
                          <h5 className="font-extrabold">Inferred Agricultural Metadata</h5>
                          <p>These values are inferred by Gemini based on the chemical content and product variety. Edit them as needed.</p>
                        </div>
                      </div>

                      {/* Soil */}
                      <div className="grid grid-cols-1 md:grid-cols-4 items-start gap-4 border-b border-gray-50 pb-4">
                        <div className="md:col-span-1 pt-2">
                          <label className="text-xs font-bold text-gray-700 uppercase tracking-widest">Recommended Soil</label>
                        </div>
                        <input
                          value={onboardingData.agricultural_metadata.recommended_soil || ""}
                          onChange={(e) => handleMetadataChange("recommended_soil", e.target.value)}
                          placeholder="Loamy, black soil, etc."
                          className="md:col-span-3 border border-gray-200 rounded-xl p-3 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
                        />
                      </div>

                      {/* Suitable Region */}
                      <div className="grid grid-cols-1 md:grid-cols-4 items-start gap-4 border-b border-gray-50 pb-4">
                        <div className="md:col-span-1 pt-2">
                          <label className="text-xs font-bold text-gray-700 uppercase tracking-widest">Suitable Region</label>
                        </div>
                        <input
                          value={onboardingData.agricultural_metadata.suitable_region || ""}
                          onChange={(e) => handleMetadataChange("suitable_region", e.target.value)}
                          placeholder="North India, All India, etc."
                          className="md:col-span-3 border border-gray-200 rounded-xl p-3 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
                        />
                      </div>

                      {/* Water Requirement */}
                      <div className="grid grid-cols-1 md:grid-cols-4 items-start gap-4 border-b border-gray-50 pb-4">
                        <div className="md:col-span-1 pt-2">
                          <label className="text-xs font-bold text-gray-700 uppercase tracking-widest">Water Requirement</label>
                        </div>
                        <input
                          value={onboardingData.agricultural_metadata.water_requirement || ""}
                          onChange={(e) => handleMetadataChange("water_requirement", e.target.value)}
                          placeholder="High, Moderate, low etc."
                          className="md:col-span-3 border border-gray-200 rounded-xl p-3 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
                        />
                      </div>

                      {/* Planting Months */}
                      <div className="grid grid-cols-1 md:grid-cols-4 items-start gap-4 border-b border-gray-50 pb-4">
                        <div className="md:col-span-1 pt-2">
                          <label className="text-xs font-bold text-gray-700 uppercase tracking-widest">Planting Months</label>
                        </div>
                        <input
                          value={onboardingData.agricultural_metadata.planting_months || ""}
                          onChange={(e) => handleMetadataChange("planting_months", e.target.value)}
                          placeholder="June - July, Oct - Nov"
                          className="md:col-span-3 border border-gray-200 rounded-xl p-3 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
                        />
                      </div>

                      {/* Harvest Months */}
                      <div className="grid grid-cols-1 md:grid-cols-4 items-start gap-4 border-b border-gray-50 pb-4">
                        <div className="md:col-span-1 pt-2">
                          <label className="text-xs font-bold text-gray-700 uppercase tracking-widest">Harvest Months</label>
                        </div>
                        <input
                          value={onboardingData.agricultural_metadata.harvest_months || ""}
                          onChange={(e) => handleMetadataChange("harvest_months", e.target.value)}
                          placeholder="Oct - Nov, March - April"
                          className="md:col-span-3 border border-gray-200 rounded-xl p-3 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
                        />
                      </div>

                      {/* Target Pest */}
                      <div className="grid grid-cols-1 md:grid-cols-4 items-start gap-4 border-b border-gray-50 pb-4">
                        <div className="md:col-span-1 pt-2">
                          <label className="text-xs font-bold text-gray-700 uppercase tracking-widest">Target Pest</label>
                        </div>
                        <input
                          value={onboardingData.agricultural_metadata.target_pest || ""}
                          onChange={(e) => handleMetadataChange("target_pest", e.target.value)}
                          placeholder="Stem borer, leaf hopper, etc."
                          className="md:col-span-3 border border-gray-200 rounded-xl p-3 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
                        />
                      </div>

                      {/* Target Disease */}
                      <div className="grid grid-cols-1 md:grid-cols-4 items-start gap-4 border-b border-gray-50 pb-4">
                        <div className="md:col-span-1 pt-2">
                          <label className="text-xs font-bold text-gray-700 uppercase tracking-widest">Target Disease</label>
                        </div>
                        <input
                          value={onboardingData.agricultural_metadata.target_disease || ""}
                          onChange={(e) => handleMetadataChange("target_disease", e.target.value)}
                          placeholder="Blast, leaf rust, etc."
                          className="md:col-span-3 border border-gray-200 rounded-xl p-3 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
                        />
                      </div>

                      {/* Recommended Dosage */}
                      <div className="grid grid-cols-1 md:grid-cols-4 items-start gap-4 border-b border-gray-50 pb-4">
                        <div className="md:col-span-1 pt-2">
                          <label className="text-xs font-bold text-gray-700 uppercase tracking-widest">Dosage</label>
                        </div>
                        <input
                          value={onboardingData.agricultural_metadata.recommended_dosage || ""}
                          onChange={(e) => handleMetadataChange("recommended_dosage", e.target.value)}
                          placeholder="2 ml/L of water, 10kg/acre etc."
                          className="md:col-span-3 border border-gray-200 rounded-xl p-3 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
                        />
                      </div>

                      {/* Seed kind/season dropdown helpers if Category is seeds */}
                      {onboardingData.fields.category.value === "seeds" && (
                        <>
                          <div className="grid grid-cols-1 md:grid-cols-4 items-start gap-4 border-b border-gray-50 pb-4">
                            <div className="md:col-span-1 pt-2">
                              <label className="text-xs font-bold text-gray-700 uppercase tracking-widest">Seed Variety</label>
                            </div>
                            <input
                              value={onboardingData.fields.seed_kind.value || ""}
                              onChange={(e) => handleFieldChange("seed_kind", e.target.value)}
                              placeholder="Paddy, wheat, maize"
                              className="md:col-span-3 border border-gray-200 rounded-xl p-3 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
                            />
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-4 items-start gap-4 border-b border-gray-50 pb-4">
                            <div className="md:col-span-1 pt-2">
                              <label className="text-xs font-bold text-gray-700 uppercase tracking-widest">Sowing Season</label>
                            </div>
                            <input
                              value={onboardingData.fields.recommended_season.value || ""}
                              onChange={(e) => handleFieldChange("recommended_season", e.target.value)}
                              placeholder="Kharif, Rabi, Rabi/Kharif"
                              className="md:col-span-3 border border-gray-200 rounded-xl p-3 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
                            />
                          </div>
                        </>
                      )}

                    </div>
                  )}

                </div>
              </div>
            </div>

            {/* Right side: Description, Tags, and Save Confirmation */}
            <div className="lg:col-span-4 space-y-6">
              
              {/* Thumbnail Selector card */}
              <div className="bg-white border border-gray-100 rounded-3xl p-6 shadow-xl space-y-4">
                <h4 className="font-extrabold text-xs text-gray-900 uppercase tracking-widest flex items-center gap-1.5">
                  <Layers size={14} className="text-teal-600" /> Catalog Thumbnail
                </h4>
                <p className="text-[10px] text-gray-400">
                  Select which image to display on the storefront catalog list. You can choose a local scanned image or an official web image found by our agent.
                </p>

                {/* Selected thumbnail preview */}
                {selectedThumbnail && (
                  <div className="relative rounded-2xl overflow-hidden border border-teal-100 bg-teal-50/20 aspect-video flex items-center justify-center">
                    <img 
                      src={selectedThumbnail.startsWith("/") ? `http://${selectedThumbnail}` : selectedThumbnail} 
                      alt="Selected Catalog Thumbnail" 
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute bottom-2 left-2 px-2 py-0.5 bg-teal-600 text-white text-[9px] font-bold rounded">
                      Selected Thumbnail
                    </div>
                  </div>
                )}

                {/* Candidate Selection Row */}
                <div className="space-y-3">
                  {/* Scanned Images Options */}
                  <div className="space-y-1">
                    <span className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Scanned Images</span>
                    <div className="flex gap-2 overflow-x-auto pb-1">
                      {onboardingData.image_urls.map((url, i) => {
                        const isSelected = selectedThumbnail === url;
                        return (
                          <button
                            key={i}
                            type="button"
                            onClick={() => setSelectedThumbnail(url)}
                            className={`relative h-14 w-20 flex-shrink-0 rounded-lg overflow-hidden border-2 transition ${
                              isSelected ? "border-teal-600 shadow" : "border-gray-200 opacity-60 hover:opacity-100"
                            }`}
                          >
                            <img src={`http://${url}`} className="w-full h-full object-cover" />
                            {isSelected && (
                              <div className="absolute inset-0 bg-teal-600/15 flex items-center justify-center">
                                <span className="p-0.5 bg-teal-600 text-white rounded-full">
                                  <Check size={8} strokeWidth={3} />
                                </span>
                              </div>
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Web Image Options */}
                  {onboardingData.web_image_urls && onboardingData.web_image_urls.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Web Product Images</span>
                      <div className="flex gap-2 overflow-x-auto pb-1">
                        {onboardingData.web_image_urls.map((url, i) => {
                          const isSelected = selectedThumbnail === url;
                          return (
                            <button
                              key={i}
                              type="button"
                              onClick={() => setSelectedThumbnail(url)}
                              className={`relative h-14 w-20 flex-shrink-0 rounded-lg overflow-hidden border-2 transition ${
                                isSelected ? "border-teal-600 shadow" : "border-gray-200 opacity-60 hover:opacity-100"
                              }`}
                            >
                              <img src={url} className="w-full h-full object-cover" referrerPolicy="no-referrer" />
                              {isSelected && (
                                <div className="absolute inset-0 bg-teal-600/15 flex items-center justify-center">
                                  <span className="p-0.5 bg-teal-600 text-white rounded-full">
                                    <Check size={8} strokeWidth={3} />
                                  </span>
                                </div>
                              )}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Custom URL Input option */}
                  <div className="space-y-1">
                    <span className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Custom Image URL</span>
                    <input
                      type="text"
                      value={selectedThumbnail}
                      onChange={(e) => setSelectedThumbnail(e.target.value)}
                      placeholder="Paste any product image URL..."
                      className="w-full border border-gray-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-teal-500"
                    />
                  </div>
                </div>
              </div>

              {/* Product description card */}
              <div className="bg-white border border-gray-100 rounded-3xl p-6 shadow-xl space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-extrabold text-xs text-gray-900 uppercase tracking-widest flex items-center gap-1">
                    <FileText size={14} className="text-teal-600" /> Factual Description
                  </h4>
                  <span className="text-[10px] text-gray-400 bg-gray-100 px-2 py-0.5 rounded font-bold">
                    {onboardingData.fields.description.confidence}% conf
                  </span>
                </div>
                <textarea
                  value={onboardingData.fields.description.value || ""}
                  onChange={(e) => handleFieldChange("description", e.target.value)}
                  rows={4}
                  className="w-full border border-gray-200 rounded-2xl p-3 text-xs text-gray-800 focus:outline-none focus:ring-2 focus:ring-teal-500 resize-none leading-relaxed"
                  placeholder="Professional agronomic product description..."
                />
                <p className="text-[10px] text-gray-400 font-medium italic">
                  Keep descriptions dry, scientific and helpful to farmers. No marketing embellishments allowed.
                </p>
              </div>

              {/* Tag Manager card */}
              <div className="bg-white border border-gray-100 rounded-3xl p-6 shadow-xl space-y-4">
                <h4 className="font-extrabold text-xs text-gray-900 uppercase tracking-widest flex items-center gap-1.5">
                  <Tag size={14} className="text-teal-600" /> Searchable tags
                </h4>
                
                {/* Tag pill list */}
                <div className="flex flex-wrap gap-1.5">
                  {onboardingData.tags.map((t, idx) => (
                    <span 
                      key={idx} 
                      className="inline-flex items-center gap-1 px-2.5 py-1 bg-teal-50 text-teal-700 text-xs font-bold rounded-full border border-teal-100"
                    >
                      {t}
                      <button 
                        onClick={() => removeTag(t)}
                        className="hover:text-teal-950 hover:bg-teal-200/50 rounded-full p-0.5 transition"
                      >
                        <X size={10} />
                      </button>
                    </span>
                  ))}
                  {onboardingData.tags.length === 0 && (
                    <span className="text-xs text-gray-400 italic">No search tags generated.</span>
                  )}
                </div>

                {/* Add Tag input */}
                <div className="flex gap-2 pt-2">
                  <input
                    type="text"
                    value={newTagInput}
                    onChange={(e) => setNewTagInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        addTag();
                      }
                    }}
                    placeholder="Add custom tag..."
                    className="flex-grow border border-gray-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-teal-500"
                  />
                  <button
                    onClick={addTag}
                    className="p-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl transition"
                  >
                    <Plus size={14} />
                  </button>
                </div>
              </div>

              {/* Onboard Approve & Publish Action panel */}
              <div className="bg-white border border-teal-100 rounded-3xl p-6 shadow-2xl space-y-5">
                <div className="space-y-2">
                  <h4 className="font-extrabold text-xs text-gray-900 uppercase tracking-widest">
                    Approve and Catalog
                  </h4>
                  <div className="flex items-center justify-between text-xs text-gray-600">
                    <span>Initial Inventory Stock:</span>
                    <input 
                      type="number"
                      value={stockToOnboard}
                      onChange={(e) => setStockToOnboard(Math.max(0, parseInt(e.target.value) || 0))}
                      className="w-16 p-1 border border-gray-200 rounded text-center font-bold text-gray-800"
                    />
                  </div>
                  <p className="text-[10px] text-gray-400 leading-normal">
                    This registers all the validated information, description, tags, confidence telemetry and uploads to the storefront product list.
                  </p>
                </div>

                <button
                  onClick={handleApproveAndSave}
                  disabled={onboardingData.duplicate_info.duplicate_found && !ignoreDuplicateWarning}
                  className="w-full py-4 bg-teal-600 hover:bg-teal-700 disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed text-white font-extrabold rounded-2xl transition shadow-lg text-xs uppercase tracking-widest flex items-center justify-center gap-2"
                >
                  <ShieldCheck size={16} /> Approve & Save Catalog
                </button>
              </div>

            </div>
          </div>

        </div>
      )}

      {/* Live Camera Webcam Capture Modal */}
      {cameraActive && (
        <div className="fixed inset-0 bg-black/85 flex items-center justify-center p-4 z-[999] backdrop-blur-md animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl border border-gray-100 shadow-2xl overflow-hidden max-w-lg w-full relative p-6 space-y-4 animate-in zoom-in-95 duration-200">
            
            <div className="flex items-center justify-between border-b border-gray-50 pb-2">
              <h3 className="font-extrabold text-sm text-gray-900 uppercase tracking-wider">
                Capture Product Panel
              </h3>
              <button
                type="button"
                onClick={stopCamera}
                className="text-xs text-red-500 hover:underline font-semibold"
              >
                Close Camera
              </button>
            </div>

            <div className="bg-black rounded-2xl overflow-hidden aspect-video relative flex items-center justify-center border border-gray-900">
              {cameraError ? (
                <div className="p-6 text-center space-y-3">
                  <span className="text-3xl">⚠️</span>
                  <p className="text-xs text-red-400 font-semibold leading-relaxed">{cameraError}</p>
                </div>
              ) : (
                <>
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-4 border border-dashed border-teal-500/20 pointer-events-none rounded-xl"></div>
                </>
              )}
            </div>

            <div className="flex flex-col gap-3">
              {availableDevices.length > 1 && (
                <div className="space-y-1">
                  <label className="block text-[9px] font-extrabold uppercase tracking-widest text-gray-400">Select Camera</label>
                  <select
                    value={selectedDeviceId}
                    onChange={(e) => {
                      setSelectedDeviceId(e.target.value);
                      startCamera(e.target.value);
                    }}
                    className="w-full p-2.5 bg-gray-50 border border-gray-200 rounded-xl text-xs text-gray-950 bg-white focus:outline-none"
                  >
                    {availableDevices.map((device, idx) => (
                      <option key={device.deviceId} value={device.deviceId}>
                        {device.label || `Camera ${idx + 1}`}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={stopCamera}
                  className="flex-grow py-3 bg-gray-50 hover:bg-gray-100 text-gray-700 font-bold rounded-xl text-xs active:scale-95 transition"
                >
                  Cancel
                </button>
                {!cameraError && (
                  <button
                    type="button"
                    onClick={capturePhoto}
                    className="flex-grow py-3 bg-teal-600 hover:bg-teal-700 text-white font-extrabold rounded-xl text-xs active:scale-95 transition flex items-center justify-center gap-1.5 shadow"
                  >
                    Take Photo
                  </button>
                )}
              </div>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}

// Sub-components/helpers for rendering editable fields nicely
function renderEditableField(
  id: string, 
  label: string, 
  fieldInfo: FieldInfo, 
  onChange: (id: string, value: any) => void,
  type: "text" | "textarea" = "text"
) {
  const isLowConfidence = fieldInfo.confidence < 80;
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 items-start gap-4 border-b border-gray-50 pb-4">
      <div className="md:col-span-1 pt-2">
        <label className="text-xs font-bold text-gray-700 uppercase tracking-widest">
          {label}
        </label>
      </div>
      
      <div className="md:col-span-3 space-y-1.5">
        {type === "textarea" ? (
          <textarea
            value={fieldInfo.value || ""}
            onChange={(e) => onChange(id, e.target.value)}
            rows={3}
            className={`w-full border rounded-xl p-3 text-xs focus:outline-none focus:ring-2 focus:ring-teal-500 resize-y leading-relaxed ${
              isLowConfidence ? "border-red-300 bg-red-50/10" : "border-gray-200"
            }`}
          />
        ) : (
          <input
            type="text"
            value={fieldInfo.value || ""}
            onChange={(e) => onChange(id, e.target.value)}
            className={`w-full border rounded-xl p-3 text-xs focus:outline-none focus:ring-2 focus:ring-teal-500 ${
              isLowConfidence ? "border-red-300 bg-red-50/10" : "border-gray-200"
            }`}
          />
        )}
        
        {renderFieldMetaBadge(fieldInfo)}
      </div>
    </div>
  );
}

function renderFieldMetaBadge(fieldInfo: FieldInfo) {
  const isLowConfidence = fieldInfo.confidence < 80;
  
  return (
    <div className="flex items-center gap-2 text-[10px] text-gray-400 font-medium">
      <span className={`px-1.5 py-0.5 rounded font-extrabold ${
        isLowConfidence 
          ? "bg-red-50 text-red-600 border border-red-100" 
          : "bg-green-50 text-emerald-700 border border-green-100"
      }`}>
        {fieldInfo.confidence}% Confidence
      </span>
      <span>•</span>
      <span>Source: {fieldInfo.source}</span>
    </div>
  );
}
