import { useEffect, useState } from "react";
import { getAccessToken } from "../../api/client";
import { getCurrentSubdomain } from "../../lib/subdomain";
import { Loader2, Image as ImageIcon } from "lucide-react";

export default function AuthImage({ src, alt, className = "", ...props }) {
  const [imgSrc, setImgSrc] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!src) return;

    let active = true;
    let objectUrl = "";

    const loadImage = async () => {
      try {
        setLoading(true);
        setError(false);
        const headers = {};
        const token = getAccessToken();
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }
        const sub = getCurrentSubdomain();
        if (sub) {
          headers["X-Tenant-Subdomain"] = sub;
        }

        const response = await fetch(src, { headers });
        if (!response.ok) {
          throw new Error("Failed to load authenticated image");
        }

        const blob = await response.blob();
        if (active) {
          objectUrl = URL.createObjectURL(blob);
          setImgSrc(objectUrl);
        }
      } catch (err) {
        console.error("Error loading authenticated image:", err);
        if (active) {
          setError(true);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    loadImage();

    return () => {
      active = false;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [src]);

  if (loading) {
    return (
      <div className={`flex flex-col items-center justify-center bg-[var(--surface-card)] rounded-md border border-[var(--hairline)] ${className}`} {...props}>
        <Loader2 className="w-6 h-6 text-[var(--mute)] animate-spin mb-2" />
        <span className="text-xs text-[var(--mute)] font-medium">Loading image...</span>
      </div>
    );
  }

  if (error || !imgSrc) {
    return (
      <div className={`flex flex-col items-center justify-center bg-[var(--surface-card)] rounded-md border-2 border-dashed border-[var(--hairline)] p-6 ${className}`} {...props}>
        <ImageIcon className="w-8 h-8 text-[var(--ash)] mb-2" />
        <span className="text-xs text-[var(--mute)] font-medium">Unable to load medical image</span>
      </div>
    );
  }

  return (
    <img
      src={imgSrc}
      alt={alt}
      className={`rounded-md object-cover transition-opacity duration-300 ${className}`}
      {...props}
    />
  );
}
