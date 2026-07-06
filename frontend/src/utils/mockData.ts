import { type Product } from "../types/product";


export interface Order {
  id: string;
  date: string;
  total: number;
  status: 'Pending' | 'Completed' | 'Processing' | 'Cancelled';
  items: {
    productId: string;
    productName: string;
    quantity: number;
    price: number;
    image: string;
  }[];
}

export const MOCK_PRODUCTS: Product[] = [
  {
    id: "prod-1",
    name: "Golden Hybrid Maize Seeds (F1)",
    category: "seeds",
    brand: "Vikas Seeds",
    price: 450,
    stock: 75,
    rating: 4.8,
    reviewsCount: 124,
    image: "https://images.unsplash.com/photo-1530595467537-0b5996c41f2d?auto=format&fit=crop&q=80&w=600",
    description: "High-yielding F1 hybrid maize seeds designed for optimal performance in diverse soil conditions. Disease resistant and drought tolerant.",
    specifications: {
      "Maturity Period": "95-100 Days",
      "Yield Potential": "25-30 Quintals/Acre",
      "Seed Rate": "8 kg/Acre",
      "Grain Color": "Bright Yellow-Orange",
      "Package Weight": "5 Kg"
    },
    kind: "maize",
    season: "kharif"
  },
  {
    id: "prod-2",
    name: "Premium Basmati Paddy Seeds (1121)",
    category: "seeds",
    brand: "Krishi Premium",
    price: 850,
    stock: 40,
    rating: 4.7,
    reviewsCount: 89,
    image: "https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&q=80&w=600",
    description: "Authentic long-grain 1121 Basmati paddy seeds. Offers exceptional elongation upon cooking and excellent aromatic characteristics.",
    specifications: {
      "Maturity Period": "135-140 Days",
      "Grain Length": "8.4 mm average",
      "Water Requirement": "Medium-High",
      "Package Weight": "10 Kg",
      "Sowing Season": "Kharif"
    },
    kind: "paddy",
    season: "kharif"
  },
  {
    id: "prod-3",
    name: "NPK Water Soluble Fertilizer 19:19:19",
    category: "fertilizers",
    brand: "Mahadhan",
    price: 180,
    stock: 120,
    rating: 4.6,
    reviewsCount: 310,
    image: "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?auto=format&fit=crop&q=80&w=600",
    description: "Fully water-soluble balanced fertilizer containing nitrogen, phosphorus, and potassium. Promotes healthy vegetative growth and strong root systems.",
    specifications: {
      "Composition": "N-19%, P-19%, K-19%",
      "Form": "Powder",
      "Application Type": "Foliar Spray / Drip Irrigation",
      "Package Weight": "1 Kg",
      "Suitable Crops": "All Crops"
    }
  },
  {
    id: "prod-4",
    name: "Organic Neem Cake Compost",
    category: "fertilizers",
    brand: "BioGrow",
    price: 320,
    stock: 15,
    rating: 4.9,
    reviewsCount: 45,
    image: "https://images.unsplash.com/photo-1592150621744-aca64f48394a?auto=format&fit=crop&q=80&w=600",
    description: "100% organic neem cake manure. Acts as an excellent natural fertilizer and soil conditioner, while protecting roots from nematodes and soil pests.",
    specifications: {
      "Source": "Cold-pressed Neem Seeds",
      "N-P-K Ratio": "4-1-2",
      "Organic Matter": "Min 70%",
      "Package Weight": "5 Kg",
      "Application Rate": "250g per plant"
    }
  },
  {
    id: "prod-5",
    name: "Broad Spectrum Weed-Out Herbicide",
    category: "herbicides",
    brand: "CropSafe",
    price: 640,
    stock: 0,
    rating: 4.5,
    reviewsCount: 76,
    image: "https://images.unsplash.com/photo-1592417817098-8f3d6eb19675?auto=format&fit=crop&q=80&w=600",
    description: "Non-selective, post-emergence herbicide for control of annual and perennial weeds. Highly effective and quick-acting formula.",
    specifications: {
      "Active Ingredient": "Glyphosate 41% SL",
      "Target Weeds": "Grass, Sedge, Broadleaf weeds",
      "Dosage": "15 ml / Litre of water",
      "Package Volume": "1 Litre",
      "Precaution": "Avoid contact with crop leaves"
    }
  },
  {
    id: "prod-6",
    name: "Selective Rice Weed Killer (Pre-emergence)",
    category: "herbicides",
    brand: "Mahadhan",
    price: 490,
    stock: 60,
    rating: 4.4,
    reviewsCount: 52,
    image: "https://images.unsplash.com/photo-1628352081506-83c43123ed6d?auto=format&fit=crop&q=80&w=600",
    description: "Pre-emergence herbicide selective for rice crops. Prevents growth of early weeds in paddy fields without harming young paddy shoots.",
    specifications: {
      "Active Ingredient": "Pretilachlor 50% EC",
      "Application Time": "0-3 days after transplanting",
      "Dosage": "500 ml / Acre",
      "Package Volume": "500 ml",
      "Suitable Crops": "Paddy"
    }
  },
  {
    id: "prod-7",
    name: "Organic Neem Shield Pesticide",
    category: "pesticides",
    brand: "BioGrow",
    price: 280,
    stock: 85,
    rating: 4.8,
    reviewsCount: 156,
    image: "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?auto=format&fit=crop&q=80&w=600",
    description: "Eco-friendly, cold-pressed Neem Oil pesticide emulsified for foliar spray. Controls aphids, whiteflies, thrips, spider mites, and leaf miners.",
    specifications: {
      "Active Ingredient": "Azadirachtin 1500 PPM",
      "Organic Certified": "Yes",
      "Dilution": "5 ml / Litre of water",
      "Package Volume": "250 ml",
      "Residual Effect": "None (Safe for harvest in 24 hours)"
    }
  },
  {
    id: "prod-8",
    name: "Termite & Sucking Pest Killer",
    category: "pesticides",
    brand: "Syngenta",
    price: 790,
    stock: 50,
    rating: 4.7,
    reviewsCount: 204,
    image: "https://images.unsplash.com/photo-1516253593875-bd7ba052fbc5?auto=format&fit=crop&q=80&w=600",
    description: "Highly effective systemic insecticide with dual action. Ideal for protection against termites, whitegrubs, jassids, and thrips.",
    specifications: {
      "Active Ingredient": "Thiamethoxam 25% WG",
      "Form": "Water Dispersible Granules",
      "Target Pests": "Termites, Aphids, Jassids, Whiteflies",
      "Package Weight": "250 g",
      "Safety Profile": "Class III (Slightly Hazardous)"
    }
  }
];

export const MOCK_ORDERS: Order[] = [
  {
    id: "ORD-9823",
    date: "2026-06-20",
    total: 1080,
    status: "Completed",
    items: [
      {
        productId: "prod-3",
        productName: "NPK Water Soluble Fertilizer 19:19:19",
        quantity: 2,
        price: 180,
        image: "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?auto=format&fit=crop&q=80&w=600"
      },
      {
        productId: "prod-8",
        productName: "Termite & Sucking Pest Killer",
        quantity: 1,
        price: 790,
        image: "https://images.unsplash.com/photo-1516253593875-bd7ba052fbc5?auto=format&fit=crop&q=80&w=600"
      }
    ]
  },
  {
    id: "ORD-8451",
    date: "2026-06-22",
    total: 1700,
    status: "Processing",
    items: [
      {
        productId: "prod-2",
        productName: "Premium Basmati Paddy Seeds (1121)",
        quantity: 2,
        price: 850,
        image: "https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&q=80&w=600"
      }
    ]
  },
  {
    id: "ORD-7612",
    date: "2026-06-23",
    total: 730,
    status: "Pending",
    items: [
      {
        productId: "prod-1",
        productName: "Golden Hybrid Maize Seeds (F1)",
        quantity: 1,
        price: 450,
        image: "https://images.unsplash.com/photo-1530595467537-0b5996c41f2d?auto=format&fit=crop&q=80&w=600"
      },
      {
        productId: "prod-7",
        productName: "Organic Neem Shield Pesticide",
        quantity: 1,
        price: 280,
        image: "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?auto=format&fit=crop&q=80&w=600"
      }
    ]
  }
];

export const MOCK_TESTIMONIALS = [
  {
    id: 1,
    name: "Ramesh Choudhary",
    location: "Karnal, Haryana",
    role: "Wheat & Paddy Farmer",
    text: "I bought Basmati Paddy seeds from Vikas Beej Bhandar last season. The germination rate was close to 95%, and the yield was the highest I've had in 5 years. Truly recommend KrishiSathi!",
    image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&q=80&w=150"
  },
  {
    id: 2,
    name: "Baldev Singh",
    location: "Bathinda, Punjab",
    role: "Cotton & Maize Farmer",
    text: "The AI assistant helped me identify a leaf pest on my cotton crop in seconds. I purchased the suggested pesticide from this app, and it was delivered within 24 hours. Phenomenal service!",
    image: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&q=80&w=150"
  },
  {
    id: 3,
    name: "Savita Patil",
    location: "Nashik, Maharashtra",
    role: "Horticulture Farmer (Grapes)",
    text: "Finding high-quality selective herbicides and NPK fertilizers in one place is hard. KrishiSathi makes it simple. Excellent pricing, fast delivery, and quality guarantee.",
    image: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=150"
  }
];
