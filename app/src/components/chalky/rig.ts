// Chalky's mood rig: ported 1:1 from chalky() in docs/scraper/dashboard-handoff/design/run-console.dc.html (same as the mascot sheet).

export type MoodKey = 'warm' | 'jog' | 'sprint' | 'final' | 'done' | 'hurt' | 'fail'

export interface Mood {
  name: string
  rule: string
  color: string
  glow: string
  anim: string
  spd: string
  legs: string
  armL: string
  armR: string
  swingL: string
  swingR: string
  fists?: boolean
  fxL?: number
  fyL?: number
  fxR?: number
  fyR?: number
  eyesOpen?: boolean
  eyeRx: number
  eyeRy?: number
  shine: number
  sparkle?: boolean
  eyepop?: boolean
  starEyes?: boolean
  eyesHappy?: boolean
  eyesX?: boolean
  brows: string
  mouth: string
  mouthFill: string
  teeth?: boolean
  teethD?: string
  tongueCy?: number
  tongueRx?: number
  sweat?: boolean
  speed?: boolean
  headband?: boolean
  blush?: boolean
  sparkles?: boolean
  bob?: boolean
  pulse?: boolean
  confetti?: boolean
  zz?: boolean
  bandage?: boolean
  stars?: boolean
  tear?: boolean
  plaster?: boolean
  card?: boolean
  lines: [string, string, string]
}

type MoodDef = Omit<Mood, 'eyeRx' | 'shine'> & { eyeRx?: number; shine?: number }

const DEFS: Record<MoodKey, MoodDef> = {
  warm: { name: 'Warming up', rule: '0–9%', color: '#7FA7D9', glow: 'rgba(127,167,217,0.30)', anim: 'sway', spd: '3s',
    legs: 'legs-still', armL: 'M56 108 Q 40 80 54 50', armR: 'M164 110 Q 186 116 194 134', swingL: '', swingR: '',
    eyesOpen: true, eyeRy: 2.5, brows: 'M80 84 Q 90 82 100 84 M120 84 Q 130 82 140 84',
    mouth: 'M104 124 a6 7 0 1 0 12 0 a6 7 0 1 0 -12 0', mouthFill: '#1E2A24', zz: true, blush: true,
    lines: ['Lacing the boots…', 'Checking the cache first.', 'Dry run? I’m just stretching.'] },
  jog: { name: 'Jogging', rule: '10–49%', color: '#4C8DDB', glow: 'rgba(76,141,219,0.32)', anim: 'bounce', spd: '.6s',
    legs: 'legs-run', armL: 'M56 112 Q 38 120 34 140', armR: 'M164 112 Q 184 100 190 82', swingL: 'swing-l', swingR: 'swing-r',
    eyesOpen: true, eyeRy: 8, brows: 'M80 82 L100 85 M140 82 L120 85',
    mouth: 'M98 120 Q 110 129 122 120', mouthFill: 'none', sweat: true,
    lines: ['Jogging through the requests.', 'Nice and steady, one a second.', 'Pacing myself for 90 minutes.'] },
  sprint: { name: 'Sprinting', rule: '50–89%', color: '#45B87F', glow: 'rgba(69,184,127,0.38)', anim: 'hype', spd: '.42s',
    legs: 'legs-run', armL: 'M56 106 Q 38 92 32 70', armR: 'M164 106 Q 182 92 188 70', swingL: 'pump-l', swingR: 'pump-r',
    fists: true, fxL: 32, fyL: 68, fxR: 188, fyR: 68,
    eyesOpen: true, eyeRx: 10, eyeRy: 11, shine: 3.4, sparkle: true, eyepop: true,
    brows: 'M78 80 Q 90 70 102 78 M142 80 Q 130 70 118 78',
    mouth: 'M92 114 Q 110 142 128 114 Z', mouthFill: '#1E2A24',
    teeth: true, teethD: 'M95 114.6 L125 114.6 L123 120 L97 120 Z', tongueCy: 124, tongueRx: 8,
    sweat: true, speed: true, headband: true, blush: true, sparkles: true, bob: true,
    lines: ['Second half! LET’S GOOO!', 'Eight lanes open, wheee!', 'Every cache hit is an assist!'] },
  final: { name: 'Ignited', rule: '90–99% · power-up', color: '#FFD54A', glow: 'rgba(255,200,60,0.55)', anim: 'frenzy', spd: '.34s',
    legs: 'legs-run', armL: 'M56 104 Q 40 72 40 44', armR: 'M164 104 Q 180 72 180 44', swingL: 'pump-l', swingR: 'pump-r',
    fists: true, fxL: 40, fyL: 42, fxR: 180, fyR: 42,
    eyesOpen: false, starEyes: true, eyeRy: 10,
    brows: 'M77 78 Q 90 66 103 76 M143 78 Q 130 66 117 76',
    mouth: 'M88 112 Q 110 148 132 112 Z', mouthFill: '#1E2A24',
    teeth: true, teethD: 'M91 112.6 L129 112.6 L127 119 L93 119 Z', tongueCy: 126, tongueRx: 10,
    sweat: true, speed: true, headband: true, pulse: true, blush: true, sparkles: true, bob: true,
    lines: ['AAAARGH! Power level rising!!', 'Player IDs? Over 9,000!!', 'Injury time. FINAL FORM!'] },
  done: { name: 'Full time', rule: '100%', color: '#F2C14E', glow: 'rgba(242,193,78,0.46)', anim: 'jump', spd: '.8s',
    legs: 'legs-still', armL: 'M56 104 Q 40 70 36 38', armR: 'M164 104 Q 180 70 184 38', swingL: 'pump-l', swingR: 'pump-r',
    fists: true, fxL: 36, fyL: 36, fxR: 184, fyR: 36,
    eyesOpen: false, eyesHappy: true, brows: 'M80 78 Q 90 68 100 78 M120 78 Q 130 68 140 78',
    mouth: 'M88 112 Q 110 150 132 112 Z', mouthFill: '#1E2A24',
    teeth: true, teethD: 'M91 112.6 L129 112.6 L127 119 L93 119 Z', tongueCy: 128, tongueRx: 10,
    confetti: true, blush: true, sparkles: true, bob: true,
    lines: ['FULL TIME!! Data’s in the net!', 'WHAT. A. RUN!', 'Every response saved raw. Lap of honour!'] },
  hurt: { name: 'Took a knock', rule: 'paused · WAF back-off', color: '#E07B39', glow: 'rgba(224,123,57,0.32)', anim: 'wobble', spd: '2.2s',
    legs: 'legs-still', armL: 'M56 114 Q 44 132 46 152', armR: 'M164 104 Q 180 70 150 50', swingL: '', swingR: '',
    eyesOpen: false, eyesX: true, brows: 'M80 86 L100 80 M140 86 L120 80',
    mouth: 'M96 124 Q 101 119 106 124 Q 111 129 116 124 Q 121 119 124 124', mouthFill: 'none', bandage: true, stars: true,
    lines: ['Ouch, a WAF knock.', 'Sixty seconds with the ice pack.', 'Back on at half speed.'] },
  fail: { name: 'Red card', rule: 'failures after the run', color: '#E5636B', glow: 'rgba(229,99,107,0.32)', anim: 'slump', spd: '3s',
    legs: 'legs-still', armL: 'M56 116 Q 46 136 44 156', armR: 'M164 114 Q 178 118 184 104', swingL: '', swingR: '',
    eyesOpen: true, eyeRy: 6, brows: 'M80 86 Q 90 80 100 78 M140 86 Q 130 80 120 78',
    mouth: 'M98 128 Q 110 118 122 128', mouthFill: 'none', tear: true, plaster: true, card: true,
    lines: ['Red card… requests failed.', 'Re-queue me, coach!', 'I’ll get them on the retry.'] },
}

export const MOODS: Record<MoodKey, Mood> = Object.fromEntries(
  Object.entries(DEFS).map(([key, m]) => [key, { ...m, eyeRx: m.eyeRx ?? 9, shine: m.shine ?? 2.8 }]),
) as Record<MoodKey, Mood>

export const MOOD_ORDER: MoodKey[] = ['warm', 'jog', 'sprint', 'final', 'done', 'hurt', 'fail']

/** State machine, priority top to bottom (HANDOFF section 5). */
export function moodFor(p: number, hurt: boolean, fail: boolean): MoodKey {
  return fail ? 'fail' : hurt ? 'hurt' : p >= 100 ? 'done' : p >= 90 ? 'final' : p >= 50 ? 'sprint' : p >= 10 ? 'jog' : 'warm'
}

export type Aura = 'none' | 'charge' | 'ignite' | 'glow'

export function auraFor(p: number, hurt: boolean, fail: boolean): Aura {
  return hurt || fail ? 'none' : p >= 100 ? 'glow' : p >= 90 ? 'ignite' : p >= 75 ? 'charge' : 'none'
}

const EMBER_FILLS = ['#FFE27A', '#FFF6C8', '#FFB020']
export const EMBERS = Array.from({ length: 14 }, (_, i) => ({
  x: 40 + ((i * 53) % 140), y: 150 + ((i * 17) % 50), r: (1.8 + (i % 3) * 0.9).toFixed(1),
  fill: EMBER_FILLS[i % 3], d: ((i * 0.11) % 1.4).toFixed(2) + 's',
}))

const CONFETTI_FILLS = ['#F2C14E', '#45B87F', '#4C8DDB', '#E5636B', '#E9D98B', '#B7A2F0', '#F1ECDF']
export const CONFETTI = Array.from({ length: 14 }, (_, i) => ({
  x: 14 + ((i * 47) % 196), y: -10 + ((i * 29) % 40), w: i % 3 ? 6 : 9, h: i % 2 ? 10 : 6,
  fill: CONFETTI_FILLS[i % CONFETTI_FILLS.length], d: ((i * 0.13) % 1.9).toFixed(2) + 's',
}))

export const RING_LENGTH = 364.4
