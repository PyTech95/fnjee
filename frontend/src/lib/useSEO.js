import { useEffect } from "react";

/**
 * useSEO — imperatively sets <title>, <meta name="description">, canonical,
 * OG tags, and injects JSON-LD structured data. Cleans up JSON-LD on unmount.
 */
export function useSEO({ title, description, canonical, ogImage, jsonLd }) {
  useEffect(() => {
    if (title) document.title = title;

    const upsert = (selector, create) => {
      let el = document.head.querySelector(selector);
      if (!el) { el = create(); document.head.appendChild(el); }
      return el;
    };

    if (description) {
      const el = upsert('meta[name="description"]', () => {
        const m = document.createElement("meta"); m.name = "description"; return m;
      });
      el.setAttribute("content", description);
    }
    if (canonical) {
      const el = upsert('link[rel="canonical"]', () => {
        const l = document.createElement("link"); l.rel = "canonical"; return l;
      });
      el.setAttribute("href", canonical);
    }
    const setOg = (property, content) => {
      if (!content) return;
      const el = upsert(`meta[property="${property}"]`, () => {
        const m = document.createElement("meta"); m.setAttribute("property", property); return m;
      });
      el.setAttribute("content", content);
    };
    setOg("og:title", title);
    setOg("og:description", description);
    setOg("og:type", "website");
    if (ogImage) setOg("og:image", ogImage);

    const scripts = [];
    if (jsonLd) {
      const items = Array.isArray(jsonLd) ? jsonLd : [jsonLd];
      items.forEach((data) => {
        const s = document.createElement("script");
        s.type = "application/ld+json";
        s.text = JSON.stringify(data);
        document.head.appendChild(s);
        scripts.push(s);
      });
    }
    return () => scripts.forEach((s) => s.remove());
  }, [title, description, canonical, ogImage, JSON.stringify(jsonLd)]);
}
