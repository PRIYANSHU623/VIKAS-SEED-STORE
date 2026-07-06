import { useEffect, useState } from "react";

import ProductCard from "../../components/product/ProductCard";

import { getProducts } from "../../api/productApi";

export default function Products() {
  const [products, setProducts] =useState([]);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    const data = await getProducts();
    setProducts(data);
  };

  return (
    <div className="grid grid-cols-3 gap-4">
      {products.map((product: any) => (
        <ProductCard
          key={product.id}
          product={product}
        />
      ))}
    </div>
  );
}