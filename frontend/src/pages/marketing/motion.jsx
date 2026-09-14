import { useRef, useEffect, useState } from "react";
import { motion, useInView, useReducedMotion, animate } from "framer-motion";

const EASE = [0.22, 1, 0.36, 1];

export function Reveal({ children, delay = 0, y = 24, className, as = "div", ...rest }) {
  const reduce = useReducedMotion();
  const M = motion[as] || motion.div;
  return (
    <M
      className={className}
      initial={reduce ? false : { opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.6, ease: EASE, delay }}
      {...rest}
    >
      {children}
    </M>
  );
}

export function Stagger({ children, className, delay = 0, gap = 0.08, ...rest }) {
  return (
    <motion.div
      className={className}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: "-60px" }}
      variants={{ hidden: {}, show: { transition: { staggerChildren: gap, delayChildren: delay } } }}
      {...rest}
    >
      {children}
    </motion.div>
  );
}

export function StaggerItem({ children, className, y = 22, ...rest }) {
  return (
    <motion.div
      className={className}
      variants={{ hidden: { opacity: 0, y }, show: { opacity: 1, y: 0, transition: { duration: 0.55, ease: EASE } } }}
      {...rest}
    >
      {children}
    </motion.div>
  );
}

/* Animated number counter. Parses leading numeric part, keeps prefix/suffix. */
export function Counter({ value, className }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const reduce = useReducedMotion();
  const match = String(value).match(/^([^\d]*)([\d,.]+)(.*)$/);
  const prefix = match ? match[1] : "";
  const rawNum = match ? match[2].replace(/,/g, "") : "0";
  const suffix = match ? match[3] : "";
  const target = parseFloat(rawNum) || 0;
  const decimals = (rawNum.split(".")[1] || "").length;
  const [display, setDisplay] = useState(reduce ? rawNum : "0");

  useEffect(() => {
    if (!inView || reduce) { if (reduce) setDisplay(formatNum(target, decimals)); return; }
    const controls = animate(0, target, {
      duration: 1.6,
      ease: EASE,
      onUpdate: (v) => setDisplay(formatNum(v, decimals)),
    });
    return () => controls.stop();
  }, [inView, target, decimals, reduce]);

  return <span ref={ref} className={className}>{prefix}{display}{suffix}</span>;
}

function formatNum(v, decimals) {
  const n = decimals ? v.toFixed(decimals) : Math.round(v).toString();
  const [int, dec] = n.split(".");
  const withCommas = int.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return dec ? `${withCommas}.${dec}` : withCommas;
}

export function Marquee({ items, render, className }) {
  const doubled = [...items, ...items];
  return (
    <div className={`mkt-marquee overflow-hidden ${className || ""}`}>
      <div className="mkt-marquee-track">
        {doubled.map((it, i) => (
          <div key={i} className="shrink-0">{render(it, i)}</div>
        ))}
      </div>
    </div>
  );
}
