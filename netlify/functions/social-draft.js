// Scheduled Netlify Function — generates a Reads X post draft twice a day
// and pushes it to your phone via ntfy.sh (https://ntfy.sh), a free
// no-signup push notification service: any HTTPS POST to
// https://ntfy.sh/<your-topic> shows up as a push notification on any
// phone subscribed to that topic in the ntfy app. No API keys, no email
// deliverability/domain setup, works the moment you install the app.
//
// This is the cloud twin of reads-social-agent/generate_draft.py on the
// Mac — same playbook data, same logic — except this runs on Netlify's
// infrastructure on a real schedule (see netlify.toml), so it fires
// whether or not any Mac is turned on. Deliberately zero npm dependencies
// (plain fetch, built into Node 18+ on Netlify) so it deploys with the
// site's normal drag-and-drop flow — no separate build/install step.
//
// Setup required (one-time, see nfl-trivia/netlify/README.md):
// set the NTFY_TOPIC environment variable in Netlify's site settings to
// whatever topic name you pick, and subscribe to that same topic in the
// ntfy app on your phone.

const WEEKLY_RHYTHM = [
  { day: 'Sunday', contentType: 'NFL Focus + Weekly Wrap', goal: 'Capture NFL audience + weekly summary',
    angle: 'Sunday Night knowledge check + weekly leaderboard mention', notes: 'Good day for bigger picture posts',
    templates: ['social_proof', 'weekend_energy'] },
  { day: 'Monday', contentType: 'Weekend Recap + Tough Challenge', goal: 'Re-engage after weekend games',
    angle: 'Hardest Grid from the weekend – anyone go perfect?', notes: 'Post strong user or personal results',
    templates: ['hardest_of_week', 'personal_result'] },
  { day: 'Tuesday', contentType: 'Light / Educational or Rest', goal: 'Stay present without forcing',
    angle: 'Quick tip, behind-the-scenes, or "question of the day"', notes: 'Lower volume day is fine',
    templates: ['question_hook', 'simple_cta'] },
  { day: 'Wednesday', contentType: 'Mid-Week Challenge', goal: 'Habit reinforcement',
    angle: 'Hump day Speed Round – how high can you streak?', notes: 'Good day for longer Reddit posts',
    templates: ['streak_habit', 'challenge_dare'] },
  { day: 'Thursday', contentType: 'Preview / Anticipation', goal: 'Build weekend excitement',
    angle: 'Rivalry week is coming – sharpen your knowledge', notes: 'Tie to upcoming big games',
    templates: ['question_hook', 'team_pride'] },
  { day: 'Friday', contentType: 'Get Ready / Light Challenge', goal: 'Weekend setup',
    angle: 'One more before the games – Daily Challenge is live', notes: 'Keep it energetic',
    templates: ['simple_cta', 'weekend_energy'] },
  { day: 'Saturday', contentType: 'Live CFB Energy', goal: 'Real-time relevance',
    angle: 'Share cards + reactions during/after big games', notes: 'Highest potential engagement day for CFB',
    templates: ['weekend_energy', 'personal_result'] }
];

// [startMonth, startDay, endMonth, endDay, moment, opportunity, modes, extra, priority]
const SEASONAL_MOMENTS = [
  [8, 18, 9, 7, 'Season Kickoff', '"Ball knowledge season is here" launch energy', 'All modes, especially Daily + Grid', 'Welcome series, first leaderboard push', 'Critical'],
  [10, 1, 11, 30, 'Rivalry Weeks', 'Team pride + bragging rights content', 'Team-tilted quizzes, Grid', '"Your rival\'s fans vs you" framing', 'High'],
  [12, 1, 12, 7, 'Conference Championships', 'High-stakes knowledge checks', 'IQ Test, Speed, Blitz', 'Conference-specific challenge packs', 'High'],
  [12, 8, 1, 20, 'CFP / Playoffs', 'Peak CFB attention', 'All modes + special playoff packs if possible', '"Road to the title" knowledge series', 'Critical'],
  [1, 1, 2, 7, 'NFL Playoffs', 'Peak NFL attention', 'NFL modes heavy', 'Super Bowl week special challenge', 'Critical'],
  [2, 1, 2, 14, 'Super Bowl Week', 'Maximum mainstream attention', 'NFL Quiz, Silhouette, IQ, Grid', 'Biggest share-card push of the year', 'Critical'],
  [3, 1, 4, 30, 'Draft Season', 'Off-season engagement', 'History, players, college-to-pro', 'Keep the core users warm', 'Medium'],
  [7, 1, 8, 17, 'Fall Camp / Preseason', 'Next season anticipation', 'Returning Daily Challenge energy', 'Tease new features or question banks', 'High']
];

const EIGHT_WEEK_PLAN_START = [8, 18];
const EIGHT_WEEK_PLAN = [
  { week: 'Week 0 (Pre-Season)', theme: 'Foundation & Soft Launch', tasks: 'Post 5-7 high-quality personal share cards on X. Soft drop in 2-3 relevant subreddits (value-first). DM 5-8 mid-tier CFB/NFL accounts for early feedback.' },
  { week: 'Week 1', theme: 'Season Kickoff Energy', tasks: 'Daily X posts with share cards. "Season is here" thread. Light Reddit presence in r/CFB and team subs.' },
  { week: 'Week 2', theme: 'Habit Formation', tasks: 'Consistent Mon/Wed/Fri/Sun posting cadence begins. First "Hardest Grid of the Week" post. Engage heavily in replies.' },
  { week: 'Week 3', theme: 'Social Proof Push', tasks: 'Share user results (with permission) or anonymized strong scores. "Can you beat this rating?" posts.' },
  { week: 'Week 4', theme: 'Creator Seeding', tasks: 'Send personal notes + exclusive access to 10-15 mid-tier accounts. Continue daily X cadence.' },
  { week: 'Week 5', theme: 'Rivalry & Team Pride', tasks: 'Rivalry week themed posts. "Alabama fans vs everyone" style light competition posts.' },
  { week: 'Week 6', theme: 'Retention Deep Dive', tasks: '"How\'s your Football Rating?" engagement posts. User-generated content reposts (with credit).' },
  { week: 'Week 7', theme: 'Mid-Season Momentum', tasks: 'Strong weekend coverage (Saturday CFB + Sunday NFL). Collaborate with 1-2 complementary accounts.' },
  { week: 'Week 8', theme: 'Systemize & Scale What Works', tasks: 'Double down only on the 2-3 content formats that performed best. Thank and engage top sharers.' }
];

const X_TEMPLATES = {
  personal_result: { label: 'Personal Result Share', when: 'After any strong round',
    copy: 'Just went [score/result] on the [Mode Name].\n\nFootball Rating update: [Rating]\n\nCan you beat it?\n→ getreads.netlify.app',
    tips: 'Best performing format. Always include the share card image.' },
  challenge_dare: { label: 'Challenge / Dare', when: 'When you want engagement',
    copy: "Bet you can't go perfect on today's Daily Challenge.\n\nI'm at [your result]. Drop yours.\n\ngetreads.netlify.app",
    tips: 'Works well on competitive days. Reply to people who post scores.' },
  hardest_of_week: { label: 'Hardest of the Week', when: 'Mondays or mid-week',
    copy: 'Hardest Grid of the week so far.\n\nOnly [X]% are clearing it clean.\n\nYour move → getreads.netlify.app',
    tips: 'Creates curiosity and FOMO. Use real difficulty when possible.' },
  team_pride: { label: 'Team Pride', when: 'When team personalization is live',
    copy: "[Team] fans only.\n\nWhat's your Football Rating looking like right now?\n\nMine's at [Rating] — drop yours.\n\ngetreads.netlify.app",
    tips: 'Excellent for local / team communities. Use your Alabama angle.' },
  weekend_energy: { label: 'Weekend Energy (Sat/Sun)', when: 'Game days',
    copy: 'Games are on and the Daily Challenge is live.\n\nSharpen up before kickoff.\n\ngetreads.netlify.app',
    tips: 'Short and timely. Post before or between games.' },
  streak_habit: { label: 'Streak / Habit', when: 'When highlighting consistency',
    copy: "[X] day streak on the Daily Challenge.\n\nThis is how you actually get better at ball knowledge.\n\nJoin → getreads.netlify.app",
    tips: "Sells the habit, not just a one-off score." },
  social_proof: { label: 'Social Proof', when: 'When others are sharing',
    copy: 'People are cooking on the leaderboard this week.\n\nCurrent top range is nasty.\n\nSee where you stand → getreads.netlify.app',
    tips: 'Only use when the leaderboard actually looks active.' },
  simple_cta: { label: 'Simple CTA', when: 'Low-effort consistency days',
    copy: "Today's Daily is up.\n\nGo get your rating in.\n\ngetreads.netlify.app",
    tips: "Don't overthink every post. Consistency > perfection." },
  question_hook: { label: 'Question Hook', when: 'To start conversations',
    copy: "What's the most underrated ball knowledge skill?\nA) Remembering 90s players\nB) College depth charts\nC) Super Bowl history\nD) Current stats\n\n(and yes there's a mode for all of them → getreads.netlify.app)",
    tips: 'Polls and questions boost replies. Engage with answers.' }
};

function inRange(month, day, sm, sd, em, ed) {
  const t = month * 100 + day, s = sm * 100 + sd, e = em * 100 + ed;
  return s <= e ? (t >= s && t <= e) : (t >= s || t <= e);
}

function activeSeasonalMoment(month, day) {
  for (const m of SEASONAL_MOMENTS) {
    if (inRange(month, day, m[0], m[1], m[2], m[3])) {
      return { moment: m[4], opportunity: m[5], modes: m[6], extra: m[7], priority: m[8] };
    }
  }
  return null;
}

function activeEightWeekEntry(now, chicagoParts) {
  const [sm, sd] = EIGHT_WEEK_PLAN_START;
  let start = Date.UTC(chicagoParts.year, sm - 1, sd);
  const todayUTC = Date.UTC(chicagoParts.year, chicagoParts.month - 1, chicagoParts.day);
  if (todayUTC < start) start = Date.UTC(chicagoParts.year - 1, sm - 1, sd);
  const daysIn = Math.floor((todayUTC - start) / 86400000);
  if (daysIn >= 0 && daysIn < 7 * EIGHT_WEEK_PLAN.length) return EIGHT_WEEK_PLAN[Math.floor(daysIn / 7)];
  return null;
}

// Simple deterministic pick (date-seeded) so re-runs the same day/slot don't
// reshuffle, but different days naturally rotate through a theme's options.
function pickTemplateKey(dateStr, candidates) {
  if (candidates.length === 1) return candidates[0];
  let h = 0;
  for (let i = 0; i < dateStr.length; i++) h = (h * 31 + dateStr.charCodeAt(i)) >>> 0;
  return candidates[h % candidates.length];
}

function chicagoParts(date) {
  const fmt = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Chicago', year: 'numeric', month: 'numeric', day: 'numeric',
    weekday: 'long', hour: 'numeric', hour12: false
  });
  const parts = {};
  fmt.formatToParts(date).forEach((p) => { parts[p.type] = p.value; });
  return {
    year: parseInt(parts.year, 10), month: parseInt(parts.month, 10), day: parseInt(parts.day, 10),
    weekday: parts.weekday, hour: parseInt(parts.hour, 10)
  };
}

function buildDraft(now) {
  const parts = chicagoParts(now);
  const weekdayIndex = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].indexOf(parts.weekday);
  const rhythm = WEEKLY_RHYTHM[weekdayIndex];
  const seasonal = activeSeasonalMoment(parts.month, parts.day);
  const eightWeek = activeEightWeekEntry(now, parts);
  const dateStr = `${parts.year}-${parts.month}-${parts.day}`;
  const slot = parts.hour < 14 ? 'morning' : 'evening';
  const templateKey = pickTemplateKey(dateStr, rhythm.templates);
  const template = X_TEMPLATES[templateKey];

  let msg = `${rhythm.day} (${slot}) — ${template.label}\n\n${template.copy}`;
  if (seasonal) msg += `\n\n[${seasonal.moment} is active: ${seasonal.opportunity}]`;
  if (eightWeek) msg += `\n\n[${eightWeek.week}: ${eightWeek.theme}]`;

  return { title: `Reads X draft — ${rhythm.contentType}`, message: msg, slot };
}

exports.handler = async () => {
  const topic = process.env.NTFY_TOPIC;
  if (!topic) {
    console.error('NTFY_TOPIC environment variable not set — see netlify/README.md');
    return { statusCode: 200, body: 'NTFY_TOPIC not configured, skipped.' };
  }
  const draft = buildDraft(new Date());
  try {
    await fetch(`https://ntfy.sh/${encodeURIComponent(topic)}`, {
      method: 'POST',
      headers: { Title: draft.title, Priority: 'default', Tags: 'football' },
      body: draft.message
    });
  } catch (err) {
    console.error('ntfy push failed:', err);
    return { statusCode: 500, body: 'Push failed' };
  }
  return { statusCode: 200, body: `Sent ${draft.slot} draft.` };
};
