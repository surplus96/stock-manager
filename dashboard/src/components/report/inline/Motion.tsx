"use client";

/**
 * Motion primitives — thin wrappers over framer-motion with reduced-motion
 * awareness. Centralising keeps block components small and lets the whole
 * site respect accessibility / perf preferences from one switch.
 */

import { motion, useReducedMotion, type HTMLMotionProps } from "framer-motion";
import type { PropsWithChildren } from "react";

type FadeInProps = PropsWithChildren<HTMLMotionProps<"div">> & {
  delayMs?: number;
  y?: number;
};

/** Fade + slight lift on mount, skipped for users with prefers-reduced-motion. */
export function FadeIn({ children, delayMs = 0, y = 6, ...rest }: FadeInProps) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      initial={reduced ? false : { opacity: 0, y }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: reduced ? 0 : 0.28,
        delay: reduced ? 0 : delayMs / 1000,
        ease: "easeOut",
      }}
      {...rest}
    >
      {children}
    </motion.div>
  );
}

/** Container that staggers its children. Wrap a list to get a polished
 *  sequential mount — Bloomberg-style "numbers click into place". */
export function Stagger({ children, delayMs = 0, stepMs = 60 }: PropsWithChildren<{ delayMs?: number; stepMs?: number }>) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      initial="hidden"
      animate="show"
      variants={{
        hidden: {},
        show: {
          transition: reduced
            ? {}
            : { delayChildren: delayMs / 1000, staggerChildren: stepMs / 1000 },
        },
      }}
    >
      {children}
    </motion.div>
  );
}

/** Child of <Stagger> — inherits variants so it lifts in as part of the chain. */
export function StaggerItem({ children }: PropsWithChildren) {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 6 },
        show: { opacity: 1, y: 0, transition: { duration: 0.24, ease: "easeOut" } },
      }}
    >
      {children}
    </motion.div>
  );
}
