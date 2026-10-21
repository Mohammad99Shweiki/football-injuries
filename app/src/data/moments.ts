// Injury moments in the study window (checked against news reports on 2026-10-20, see HANDOFF.md section 16).
// recur = the player had a repeat of this kind of injury. One print per player.

export interface Moment {
  lg: number
  player: string
  what: string
  area: string
  match: string
  date: string
  stamp: string
  recur: boolean
}

export const MOMENTS: Moment[] = [
  { lg: 0, player: 'Van Dijk', what: 'ACL after Pickford tackle', area: 'Knee', match: 'Everton 2–2 Liverpool', date: '17 Oct 2020', stamp: "'20 10 17", recur: false },
  { lg: 0, player: 'Elliott', what: 'fracture-dislocated ankle', area: 'Ankle', match: 'Leeds 0–3 Liverpool', date: '12 Sep 2021', stamp: "'21 09 12", recur: false },
  { lg: 0, player: 'De Bruyne', what: 'hamstring tear, surgery', area: 'Hamstring', match: 'Burnley 0–3 Man City', date: '11 Aug 2023', stamp: "'23 08 11", recur: true },
  { lg: 0, player: 'Timber', what: 'ACL on his league debut', area: 'Knee', match: 'Arsenal 2–1 Forest', date: '12 Aug 2023', stamp: "'23 08 12", recur: false },
  { lg: 1, player: 'Dembélé', what: 'hamstring tendon rupture', area: 'Hamstring', match: 'Getafe 1–2 Barcelona', date: '16 Sep 2017', stamp: "'17 09 16", recur: true },
  { lg: 1, player: 'Ansu Fati', what: 'meniscus tear', area: 'Knee', match: 'Barcelona 5–2 Betis', date: '7 Nov 2020', stamp: "'20 11 07", recur: true },
  { lg: 1, player: 'Militão', what: 'two ACLs in 15 months', area: 'Knee', match: 'v Athletic, then v Osasuna', date: '12 Aug 2023 & 9 Nov 2024', stamp: "'24 11 09", recur: true },
  { lg: 1, player: 'Alaba', what: 'ACL', area: 'Knee', match: 'Real Madrid 4–1 Villarreal', date: '17 Dec 2023', stamp: "'23 12 17", recur: false },
  { lg: 1, player: 'Carvajal', what: 'ACL', area: 'Knee', match: 'Villarreal 0–2 Real Madrid', date: '5 Oct 2024', stamp: "'24 10 05", recur: false },
  { lg: 2, player: 'Zaniolo', what: 'ACL, a second followed that year', area: 'Knee', match: 'Roma 1–2 Juventus', date: '12 Jan 2020', stamp: "'20 01 12", recur: true },
  { lg: 2, player: 'Milik', what: 'second ACL in a year', area: 'Knee', match: 'SPAL 2–3 Napoli', date: '23 Sep 2017', stamp: "'17 09 23", recur: true },
  { lg: 2, player: 'Chiesa', what: 'ACL', area: 'Knee', match: 'Roma 3–4 Juventus', date: '9 Jan 2022', stamp: "'22 01 09", recur: false },
  { lg: 3, player: 'Wirtz', what: 'ACL', area: 'Knee', match: 'Leverkusen 0–1 Köln', date: '13 Mar 2022', stamp: "'22 03 13", recur: false },
  { lg: 4, player: 'Neymar', what: 'metatarsal, later ankle surgery', area: 'Foot · Ankle', match: 'v Marseille, then v Lille', date: '25 Feb 2018 & 19 Feb 2023', stamp: "'23 02 19", recur: true },
]

const CW = 'https://commons.wikimedia.org/wiki/File:'

export interface Photo {
  img: string
  artist: string
  license: string
  page: string
}

// Same records as public/assets/credits.json (author, licence, Commons page), keyed by the print's player name.
const PHOTO: Record<string, [string, string, string, string]> = {
  'Van Dijk': ['vandijk.jpg', 'Ailura', 'CC BY-SA 3.0 AT', '20160604_AUT_NED_8876_(cropped).jpg'],
  'Elliott': ['elliott.jpg', 'crop by Indopug', 'CC BY-SA 4.0', 'Harvey_Elliott_in_2022.jpg'],
  'De Bruyne': ['debruyne.jpg', 'Bryan Berlin', 'CC BY-SA 4.0', 'Kevin_De_Bruyne_USMNT_v_Belgium_Mar_28_2026-64_(cropped).jpg'],
  'Timber': ['timber.jpg', 'Carlo Bruil Fotografie', 'CC BY 2.0', 'JURRIEN_TIMBER.jpg'],
  'Dembélé': ['dembele.jpg', 'Bryan Berlin', 'CC BY-SA 4.0', 'Ousmane_Dembele_France_v_Senegal_16_June_2026-341_(cropped)_2.jpg'],
  'Ansu Fati': ['fati.jpg', 'Olga Shcherbytska', 'CC BY-SA 4.0', '%D0%9C%D0%B0%D1%82%D1%87_%C2%AB%D0%94%D0%B8%D0%BD%D0%B0%D0%BC%D0%BE%C2%BB_-_%C2%AB%D0%91%D0%B0%D1%80%D1%81%D0%B5%D0%BB%D0%BE%D0%BD%D0%B0%C2%BB_0-1._2_%D0%BB%D0%B8%D1%81%D1%82%D0%BE%D0%BF%D0%B0%D0%B4%D0%B0_2021_%D1%80%D0%BE%D0%BA%D1%83_%E2%80%94_1289339_(cropped).jpg'],
  'Militão': ['militao.jpg', 'Werner100359', 'CC BY-SA 4.0', '%C3%89der_Milit%C3%A3o_Real_Madrid_2019.jpg'],
  'Alaba': ['alaba.jpg', 'Granada', 'CC BY-SA 4.0', '20180610_FIFA_Friendly_Match_Austria_vs._Brazil_David_Alaba_850_1632.jpg'],
  'Carvajal': ['carvajal.jpg', 'Rolandhino1', 'CC BY-SA 4.0', 'UEFA_EURO_qualifiers_Sweden_vs_Spain_20191015_Dani_Carvajal_10_(cropped).jpg'],
  'Zaniolo': ['zaniolo.jpg', 'Joe K.', 'CC BY-SA 4.0', 'Nicol%C3%B2_Zaniolo_con_l%27Italia_U19.jpg'],
  'Milik': ['milik.jpg', 'Supporterhéninois', 'CC0', 'Lens_-_Marseille_(03-02-2021)_44.jpg'],
  'Chiesa': ['chiesa.jpg', 'Kirill Venediktov', 'CC BY-SA 3.0', 'Federico_Chiesa_vs_Zenit_2021-10-20_(cropped2).jpg'],
  'Wirtz': ['wirtz.jpg', 'Bryan Berlin', 'CC BY-SA 4.0', 'Florian_Wirtz_Ecuador_v_Germany_25_June_2026-181_(cropped).jpg'],
  'Neymar': ['neymar.jpg', 'Antoine Dellenbach', 'CC BY-SA 2.0', 'Neymar_PSG.jpg'],
}

export function photoOf(player: string): Photo {
  const [file, artist, license, page] = PHOTO[player]
  return { img: `/assets/photos/${file}`, artist, license, page: CW + page }
}

export const PHOTO_CREDITS = Object.keys(PHOTO).map((player) => ({ player, ...photoOf(player) }))

export const LOGO_CREDITS = [
  ['Premier League', 'Premier_League.svg'], ['LaLiga', 'LaLiga_logo_(2023).svg'], ['Serie A', 'Logo_Serie_A_TIM_2018-2019.png'],
  ['Bundesliga', 'Bundesliga_Wordmark_(2010-2017).svg'], ['Ligue 1', 'Ligue_1_2024_Logo.png'], ['Transfermarkt', 'Transfermarkt_logo.svg'],
].map(([name, file]) => ({ name, page: CW + file }))
