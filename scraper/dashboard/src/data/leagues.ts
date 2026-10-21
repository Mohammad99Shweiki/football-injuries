// Leagues and sites as identified in the designs. Logos: public-domain (PD-textlogo) files from Wikimedia Commons,
// used only to label each league or site.
import type { SourceKey } from '../api/types'

export interface LeagueInfo {
  name: string
  short: string
  fd: string
  us: string
  tm: string
  color: string
  logo: string
}

export const LEAGUES: LeagueInfo[] = [
  { name: 'Premier League', short: 'PL', fd: 'E0', us: 'EPL', tm: 'GB1', color: 'var(--lg-pl)', logo: '/assets/logos/pl.png' },
  { name: 'La Liga', short: 'LL', fd: 'SP1', us: 'La_liga', tm: 'ES1', color: 'var(--lg-laliga)', logo: '/assets/logos/laliga.png' },
  { name: 'Serie A', short: 'SA', fd: 'I1', us: 'Serie_A', tm: 'IT1', color: 'var(--lg-seriea)', logo: '/assets/logos/seriea.png' },
  { name: 'Bundesliga', short: 'BL', fd: 'D1', us: 'Bundesliga', tm: 'L1', color: 'var(--lg-bundesliga)', logo: '/assets/logos/bundesliga.png' },
  { name: 'Ligue 1', short: 'L1', fd: 'F1', us: 'Ligue_1', tm: 'FR1', color: 'var(--lg-ligue1)', logo: '/assets/logos/ligue1.png' },
]

export const SEASON_LABELS = ['14/15', '15/16', '16/17', '17/18', '18/19', '19/20', '20/21', '21/22', '22/23', '23/24', '24/25', '25/26']

export interface SiteInfo {
  key: SourceKey
  name: string
  short: string // log tab label + accessible name
  host: string
  color: string
  logo: string | null // FD and Understat have no free logo: typeset name tile instead
  word: string
  wordSub: string
  defaultNote: string
  unit: string
}

export const SITES: Record<SourceKey, SiteInfo> = {
  fd: {
    key: 'fd', name: 'Football-Data.co.uk', short: 'Football-Data', host: 'football-data.co.uk/mmz4281',
    color: 'var(--site-fd)', logo: null, word: 'football-data', wordSub: '.co.uk',
    defaultNote: 'One CSV per league-season, saved byte-for-byte. Serie A shots include blocked shots from 2018/19.',
    unit: 'CSVs',
  },
  us: {
    key: 'us', name: 'Understat', short: 'Understat', host: 'understat.com/getLeagueData · getTeamData',
    color: 'var(--site-us)', logo: null, word: 'understat', wordSub: '',
    defaultNote: 'XHR endpoints: getLeagueData per league-season, getTeamData per team-season.',
    unit: 'league-seasons',
  },
  tm: {
    key: 'tm', name: 'Transfermarkt', short: 'Transfermarkt', host: 'tmapi.transfermarkt.technology',
    color: 'var(--site-tm)', logo: '/assets/logos/transfermarkt.png', word: 'TM', wordSub: '',
    defaultNote: 'Record + replay transport. SDK cache=None; responses keyed by method + full URL.',
    unit: 'league-seasons',
  },
}

export const SOURCE_ORDER: SourceKey[] = ['fd', 'us', 'tm']
