/**
 * VedaOrb — Phase V-UI animated avatar
 *
 * Custom SVG/CSS orb, no external assets or animation libraries. Genuinely
 * reactive rather than a canned loop: the "speaking" state is driven by
 * real TTS playback amplitude (vedaStore.audioLevel, updated via a Web
 * Audio AnalyserNode at ~60fps) rather than a fake pulse. High-frequency
 * updates bypass React's render cycle (direct store subscription -> CSS
 * variable mutation on a ref) so a full re-render doesn't fire 60x/second.
 *
 * States: idle (slow breathing) -> listening (ripple ring) -> speaking
 * (audio-reactive glow) -> thinking (rotating ring, while a request is
 * in flight). Priority when multiple are true: speaking > listening >
 * thinking > idle.
 */
import { useEffect, useRef } from 'react'
import { useVedaStore } from '../../store/vedaStore'

let styleInjected = false
function injectStyleOnce() {
  if (styleInjected || typeof document === 'undefined') return
  styleInjected = true
  const el = document.createElement('style')
  el.textContent = `
    @keyframes veda-breathe {
      0%, 100% { transform: scale(0.92); opacity: 0.78; }
      50%      { transform: scale(1.0);  opacity: 1; }
    }
    @keyframes veda-ripple {
      0%   { transform: scale(1);   opacity: 0.55; }
      100% { transform: scale(2.1); opacity: 0; }
    }
    @keyframes veda-spin {
      to { transform: rotate(360deg); }
    }
    .veda-orb {
      position: relative;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: var(--veda-size);
      height: var(--veda-size);
      flex-shrink: 0;
    }
    .veda-orb__core {
      width: 100%;
      height: 100%;
      border-radius: 50%;
      background: radial-gradient(circle at 32% 28%, #6FE3D0, #4080FF 55%, #2A5FD9 100%);
      box-shadow: 0 0 calc(var(--veda-size) * 0.28) rgba(64, 128, 255, 0.45);
      transition: transform 0.08s linear, box-shadow 0.08s linear;
      will-change: transform;
    }
    .veda-orb--idle .veda-orb__core {
      animation: veda-breathe 3.2s ease-in-out infinite;
    }
    .veda-orb--listening .veda-orb__core {
      transform: scale(1.04);
      box-shadow: 0 0 calc(var(--veda-size) * 0.4) rgba(14, 196, 160, 0.6);
    }
    .veda-orb--speaking .veda-orb__core {
      transform: scale(calc(1 + var(--veda-level, 0) * 0.32));
      box-shadow: 0 0 calc(var(--veda-size) * (0.28 + var(--veda-level, 0) * 0.35))
                  rgba(111, 227, 208, calc(0.45 + var(--veda-level, 0) * 0.4));
    }
    .veda-orb__ripple {
      position: absolute;
      inset: 0;
      border-radius: 50%;
      border: 1.5px solid #0EC4A0;
      animation: veda-ripple 1.5s ease-out infinite;
      pointer-events: none;
    }
    .veda-orb__ring {
      position: absolute;
      inset: -3px;
      border-radius: 50%;
      border: 2px solid transparent;
      border-top-color: #4080FF;
      border-right-color: #4080FF88;
      animation: veda-spin 0.9s linear infinite;
      pointer-events: none;
    }
  `
  document.head.appendChild(el)
}

type VedaVisualState = 'idle' | 'listening' | 'speaking' | 'thinking'

export function VedaOrb({ size = 32 }: { size?: number }) {
  const listening = useVedaStore(s => s.listening)
  const speaking  = useVedaStore(s => s.speaking)
  const loading   = useVedaStore(s => s.loading)
  const orbRef    = useRef<HTMLDivElement>(null)

  useEffect(injectStyleOnce, [])

  // audioLevel updates at ~60fps while speaking (real playback amplitude) --
  // subscribe directly and mutate a CSS var rather than re-rendering React
  // on every frame.
  useEffect(() => {
    return useVedaStore.subscribe(state => {
      orbRef.current?.style.setProperty('--veda-level', String(state.audioLevel))
    })
  }, [])

  const state: VedaVisualState =
    speaking ? 'speaking' : listening ? 'listening' : loading ? 'thinking' : 'idle'

  return (
    <div
      ref={orbRef}
      className={`veda-orb veda-orb--${state}`}
      style={{ ['--veda-size' as string]: `${size}px` }}
      aria-label={`Veda -- ${state}`}
    >
      <div className="veda-orb__core" />
      {state === 'listening' && <div className="veda-orb__ripple" />}
      {state === 'thinking' && <div className="veda-orb__ring" />}
    </div>
  )
}
