import { Navigate } from "react-router-dom";
import type{ ReactNode } from "react";

interface Props {
  children: ReactNode;
}

export default function AdminRoute({
  children,
}: Props
) {
  const user = JSON.parse(
    localStorage.getItem("user") || "null"
  );

  if (
    !user ||
    user.role !== "admin"
  ) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}