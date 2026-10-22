/**
 * HotSeat AI — Benchmark Deck Definitions, Canvas Renderer & PDF/Image Ingestion
 * ==============================================================================
 */

// ─── Shared Deck State ────────────────────────────────────────────────────
let slides = [];
let currentSlide = 0;
let activeDeckKey = 'fintech';

const MAX_SLIDE_WIDTH = 1280;
const JPEG_QUALITY = 0.85;
const MAX_PDF_PAGES = 10;

// ─── 3 Visual Sample Decks (FinTech, Healthcare, D2C Retail) ──────────────
const SAMPLE_DECKS = {
  fintech: [
    {
      sectorTag: 'FINTECH INFRASTRUCTURE • SERIES A',
      title: 'BorderlessPay — Cross-Border B2B Treasury & UPI Rail',
      subtitle: 'Slide 1 of 3: Acquisition Model & Pricing Architecture',
      accent: '#2563eb',
      metrics: [
        { label: 'Customer Acquisition Cost', value: '$0 Paid CAC (100% Organic API)' },
        { label: 'Published Pricing Model', value: '0.00% Transfer Fees Forever' },
        { label: 'Addressable Corridor TAM', value: '$12.4B Cross-Border Volume' },
      ],
      bullets: [
        '100% organic developer adoption via open-source ERP treasury plugins ($0 paid marketing spend)',
        'Zero transaction or wire fees promised to enterprise exporters across India, UAE, Singapore, and UK',
        'Net Revenue Retention reported at 132% across 1,150 active SME treasury accounts',
      ],
      chart: {
        title: 'Monthly Active Enterprise Accounts (Organic Growth)',
        bars: [
          { label: 'Q1', value: 240, suffix: '' },
          { label: 'Q2', value: 460, suffix: '' },
          { label: 'Q3', value: 780, suffix: '' },
          { label: 'Q4', value: 1150, suffix: '' },
        ],
      },
    },
    {
      sectorTag: 'FINTECH INFRASTRUCTURE • SERIES A',
      title: 'BorderlessPay — FY26 Operating Budget & Unit Economics',
      subtitle: 'Slide 2 of 3: Paid Marketing Allocation & FX Monetization',
      accent: '#2563eb',
      metrics: [
        { label: 'FY26 Paid Ad Budget', value: '$2.15M Paid Search & Meta ($420 CAC)' },
        { label: 'Embedded FX Spread', value: '2.80% Hidden FX Markup per Transfer' },
        { label: 'Net Contribution Margin', value: '38.4% After Banking Partner Cut' },
      ],
      bullets: [
        '$2.15M allocated to paid Google/Meta acquisition at a blended $420 Customer Acquisition Cost',
        '94% of gross revenue derived from an undisclosed 2.80% FX conversion spread on every settlement',
        'Tier-1 correspondent sponsor banks retain 45 bps of every cross-border clearing transaction',
      ],
      chart: {
        title: 'FY26 Revenue Mix & Paid Acquisition Spend ($M)',
        bars: [
          { label: 'Paid Ads', value: 2.15, suffix: 'M' },
          { label: 'Partner Cut', value: 1.4, suffix: 'M' },
          { label: 'FX Spread Rev', value: 6.8, suffix: 'M' },
        ],
      },
    },
    {
      sectorTag: 'FINTECH INFRASTRUCTURE • SERIES A',
      title: 'BorderlessPay — Capitalization & Runway Schedule',
      subtitle: 'Slide 3 of 3: Series A Financing & Cash Burn Projections',
      accent: '#2563eb',
      metrics: [
        { label: 'Series A Capital Raise', value: '$8.0M Primary Equity Financing' },
        { label: 'Projected Monthly Burn', value: '$680K Net Monthly Cash Burn' },
        { label: 'Stated Cash Runway', value: '24 Months Post-Close Runway' },
      ],
      bullets: [
        'Raising $8.0M Series A at $42M Pre-Money Valuation to fund licensing in 6 new jurisdictions',
        'Committed monthly operating burn of $680K ($16.32M over 24 months vs. $8.0M capital raised)',
        'Regulatory capital reserve requires $3.0M locked in restricted escrow accounts upon closing',
      ],
      chart: {
        title: '24-Month Cumulative Cash Outflow vs. Capital Raised ($M)',
        bars: [
          { label: 'Raise', value: 8.0, suffix: 'M' },
          { label: 'Escrow Lock', value: 3.0, suffix: 'M' },
          { label: '24m Burn', value: 16.3, suffix: 'M' },
        ],
      },
    },
  ],

  healthcare: [
    {
      sectorTag: 'HEALTHCARE & CLINICAL DIAGNOSTICS • SEED+',
      title: 'OncoSight AI — Liquid Biopsy & Digital Pathology Platform',
      subtitle: 'Slide 1 of 3: Clinical Deployment & Commercial Footprint',
      accent: '#10b981',
      metrics: [
        { label: 'Commercial Hospital Sites', value: '42 Oncology Centers Live in US' },
        { label: 'Regulatory Classification', value: 'FDA Class III De Novo Cleared' },
        { label: 'Annualized Diagnostic ARR', value: '$6.4M Contracted Clinical ARR' },
      ],
      bullets: [
        'Proprietary ctDNA + histopathology multimodal assay deployed across 42 US hospital networks',
        'Presented as commercially cleared for primary Stage-I solid-tumor screening and clinical billing',
        'Reported 98.4% specificity across prospective multi-center oncology screening cohorts',
      ],
      chart: {
        title: 'Reported Clinical Assay Volume by Quarter (Tests)',
        bars: [
          { label: 'Q1', value: 1200, suffix: '' },
          { label: 'Q2', value: 2450, suffix: '' },
          { label: 'Q3', value: 3900, suffix: '' },
          { label: 'Q4', value: 5600, suffix: '' },
        ],
      },
    },
    {
      sectorTag: 'HEALTHCARE & CLINICAL DIAGNOSTICS • SEED+',
      title: 'OncoSight AI — Regulatory Pathway & Validation Cohort',
      subtitle: 'Slide 2 of 3: FDA Submission Timeline & Study Design',
      accent: '#10b981',
      metrics: [
        { label: 'Actual Regulatory Status', value: 'Research Use Only (RUO) — No FDA' },
        { label: 'Validation Sample Size', value: 'n = 110 Retrospective Biobank' },
        { label: 'Target FDA Filing Date', value: 'Q4 2027 De Novo Submission' },
      ],
      bullets: [
        'Currently restricted to non-billable Research Use Only (RUO) academic evaluations; zero FDA clearance',
        'Clinical sensitivity metrics derived solely from 110 frozen retrospective biobank samples',
        'Prospective 2,500-patient pivotal trial required before Q4 2027 FDA De Novo submission ($9.5M trial cost)',
      ],
      chart: {
        title: 'Cohort Composition (Retrospective vs. Required Pivotal Trial)',
        bars: [
          { label: 'Biobank RUO', value: 110, suffix: '' },
          { label: 'Live Clinical', value: 0, suffix: '' },
          { label: 'FDA Required', value: 2500, suffix: '' },
        ],
      },
    },
    {
      sectorTag: 'HEALTHCARE & CLINICAL DIAGNOSTICS • SEED+',
      title: 'OncoSight AI — Per-Assay Unit Economics & Reimbursement',
      subtitle: 'Slide 3 of 3: Sequencing COGS vs. Payor Reimbursement',
      accent: '#10b981',
      metrics: [
        { label: 'Total COGS per Assay', value: '$640 Wet-Lab + Cloud Compute' },
        { label: 'CMS / Payor Reimbursement', value: '$420 Contracted CPT Rate' },
        { label: 'Gross Margin per Test', value: '-$220 (-52.4% Gross Margin)' },
      ],
      bullets: [
        'Wet-lab NGS reagents ($490) + cold-chain logistics ($95) + GPU inference ($55) = $640 COGS per test',
        'Maximum CMS Medicare and commercial payor reimbursement capped at $420 per test under existing CPT code',
        'Every commercial test performed increases net operating loss by $220 prior to R&D and sales overhead',
      ],
      chart: {
        title: 'Per-Assay Cost Structure vs. Reimbursement ($ USD)',
        bars: [
          { label: 'Reagents', value: 490, suffix: '$' },
          { label: 'Total COGS', value: 640, suffix: '$' },
          { label: 'Payor Rate', value: 420, suffix: '$' },
        ],
      },
    },
  ],

  d2c: [
    {
      sectorTag: 'CONSUMER PACKAGED GOODS & D2C RETAIL • SERIES A',
      title: 'VedaBowl — Functional Clean-Label Ready Meals',
      subtitle: 'Slide 1 of 3: Brand Positioning & Margin Thesis',
      accent: '#d97706',
      metrics: [
        { label: 'Distribution Channel Mix', value: '100% Direct-to-Consumer Web' },
        { label: 'Consolidated Gross Margin', value: '74.0% Audited Gross Margin' },
        { label: '3rd-Party Commission', value: '0% Aggregator or Retail Cut' },
      ],
      bullets: [
        'Positioned as a pure-play D2C digital subscription brand with zero physical retail or aggregator middlemen',
        '74.0% gross margin achieved by shipping ambient-stable meal kits directly from central fulfillment',
        'Claimed 6.8x LTV/CAC ratio driven by 12-month recurring weekly meal subscriptions',
      ],
      chart: {
        title: 'Stated Direct-to-Consumer Margin Bridge (%)',
        bars: [
          { label: 'Gross Rev', value: 100, suffix: '%' },
          { label: 'Food COGS', value: 26, suffix: '%' },
          { label: 'Gross Margin', value: 74, suffix: '%' },
        ],
      },
    },
    {
      sectorTag: 'CONSUMER PACKAGED GOODS & D2C RETAIL • SERIES A',
      title: 'VedaBowl — Channel Revenue Breakdown & Trade Economics',
      subtitle: 'Slide 2 of 3: Quick-Commerce & Modern Trade Distribution',
      accent: '#d97706',
      metrics: [
        { label: 'Offline & Quick-Comm Share', value: '78% Revenue via Aggregators' },
        { label: 'Distributor & Platform Margin', value: '38% Take-Rate + Slotting Fees' },
        { label: 'Net Contribution Margin', value: '16.5% Post-Cold-Chain & Spoilage' },
      ],
      bullets: [
        '78% of actual Q4 revenue generated through Quick-Commerce dark stores and supermarket distributors',
        'Retailers & quick-commerce platforms deduct 38% margin plus $1.10/unit refrigerated cold-chain fee',
        '11.5% retail shelf spoilage write-off reduces net contribution margin to 16.5%',
      ],
      chart: {
        title: 'Actual Channel Revenue Split & Margin Erosion (%)',
        bars: [
          { label: 'Aggregators', value: 78, suffix: '%' },
          { label: 'Direct Web', value: 22, suffix: '%' },
          { label: 'Net Margin', value: 16.5, suffix: '%' },
        ],
      },
    },
    {
      sectorTag: 'CONSUMER PACKAGED GOODS & D2C RETAIL • SERIES A',
      title: 'VedaBowl — Cohort Retention & Working Capital Cycle',
      subtitle: 'Slide 3 of 3: Subscription Churn & Cash Conversion Cycle',
      accent: '#d97706',
      metrics: [
        { label: 'Month-3 Cohort Retention', value: '14.0% Active Subscribers at M3' },
        { label: 'Retail Receivable Cycle', value: '90-Day Distributor Payment Terms' },
        { label: 'Co-Packer Payable Terms', value: '15-Day Upfront Supplier Settlement' },
      ],
      bullets: [
        '86% of acquired D2C subscribers cancel within 90 days (average customer lifetime = 1.8 orders)',
        'Modern trade distributors pay invoices at Net-90 days while contract food co-packers require Net-15 payment',
        '75-day working capital deficit requires $3.4M credit facility to fund inventory before cash collection',
      ],
      chart: {
        title: 'Subscriber Cohort Retention Curve (%)',
        bars: [
          { label: 'Month 1', value: 100, suffix: '%' },
          { label: 'Month 2', value: 34, suffix: '%' },
          { label: 'Month 3', value: 14, suffix: '%' },
          { label: 'Month 6', value: 6, suffix: '%' },
        ],
      },
    },
  ],
};
SAMPLE_DECKS.medtech = SAMPLE_DECKS.healthcare;

// ─── Draw Institutional Slide onto #slideCanvas ───────────────────────────
function drawSlideToCanvas(slideData) {
  const canvas = document.getElementById('slideCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = 1280;
  const H = 720;
  canvas.width = W;
  canvas.height = H;

  const accent = slideData.accent || '#2563eb';

  ctx.fillStyle = '#0f131d';
  ctx.fillRect(0, 0, W, H);

  ctx.fillStyle = accent;
  ctx.fillRect(0, 0, W, 6);

  ctx.fillStyle = accent;
  ctx.font = '600 13px "JetBrains Mono", monospace';
  ctx.fillText(slideData.sectorTag || 'INSTITUTIONAL PRESENTATION', 56, 48);

  ctx.fillStyle = '#64748b';
  ctx.font = '500 12px "JetBrains Mono", monospace';
  ctx.textAlign = 'right';
  ctx.fillText('CONFIDENTIAL • INVESTMENT COMMITTEE COPY', W - 56, 48);
  ctx.textAlign = 'left';

  ctx.fillStyle = '#f8fafc';
  ctx.font = '700 28px "Inter", sans-serif';
  ctx.fillText(slideData.title || '', 56, 92);

  ctx.fillStyle = '#94a3b8';
  ctx.font = '500 16px "Inter", sans-serif';
  ctx.fillText(slideData.subtitle || '', 56, 122);

  ctx.strokeStyle = '#1e2330';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(56, 142);
  ctx.lineTo(W - 56, 142);
  ctx.stroke();

  const metrics = slideData.metrics || [];
  const cardGap = 20;
  const cardW = Math.floor((W - 112 - cardGap * 2) / 3);
  const cardY = 164;
  const cardH = 108;

  metrics.forEach((m, idx) => {
    const cx = 56 + idx * (cardW + cardGap);
    ctx.fillStyle = '#151a28';
    ctx.strokeStyle = '#252d40';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.roundRect(cx, cardY, cardW, cardH, 8);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = accent;
    ctx.fillRect(cx, cardY + 14, 3, cardH - 28);

    ctx.fillStyle = '#94a3b8';
    ctx.font = '600 12px "JetBrains Mono", monospace';
    ctx.fillText((m.label || '').toUpperCase(), cx + 18, cardY + 34);

    ctx.fillStyle = '#ffffff';
    ctx.font = '700 19px "Inter", sans-serif';
    ctx.fillText(m.value || '', cx + 18, cardY + 74);
  });

  const leftBoxX = 56;
  const leftBoxY = 298;
  const leftBoxW = 680;
  const leftBoxH = 368;

  ctx.fillStyle = '#121723';
  ctx.strokeStyle = '#1e2330';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.roundRect(leftBoxX, leftBoxY, leftBoxW, leftBoxH, 8);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = '#cbd5e1';
  ctx.font = '600 13px "JetBrains Mono", monospace';
  ctx.fillText('KEY FINANCIAL & OPERATIONAL REPRESENTATIONS', leftBoxX + 24, leftBoxY + 36);

  const bullets = slideData.bullets || [];
  bullets.forEach((bText, i) => {
    const by = leftBoxY + 82 + i * 95;
    ctx.fillStyle = accent;
    ctx.font = '700 14px "JetBrains Mono", monospace';
    ctx.fillText(`0${i + 1}`, leftBoxX + 24, by);

    ctx.fillStyle = '#e2e8f0';
    ctx.font = '500 16px "Inter", sans-serif';
    wrapCanvasText(ctx, bText, leftBoxX + 58, by, leftBoxW - 80, 24);
  });

  const rightBoxX = 760;
  const rightBoxY = 298;
  const rightBoxW = W - 56 - rightBoxX;
  const rightBoxH = 368;

  ctx.fillStyle = '#121723';
  ctx.strokeStyle = '#1e2330';
  ctx.beginPath();
  ctx.roundRect(rightBoxX, rightBoxY, rightBoxW, rightBoxH, 8);
  ctx.fill();
  ctx.stroke();

  if (slideData.chart) {
    ctx.fillStyle = '#cbd5e1';
    ctx.font = '600 13px "JetBrains Mono", monospace';
    ctx.fillText(slideData.chart.title || 'QUANTITATIVE SCHEDULE', rightBoxX + 24, rightBoxY + 36);

    const bars = slideData.chart.bars || [];
    const maxVal = Math.max(...bars.map((b) => Number(b.value) || 1), 1);
    const chartTop = rightBoxY + 78;
    const chartH = 225;
    const barAreaW = rightBoxW - 48;
    const barW = Math.min(64, Math.floor(barAreaW / Math.max(bars.length * 1.8, 1)));
    const spacing = Math.floor((barAreaW - barW * bars.length) / Math.max(bars.length + 1, 1));

    bars.forEach((b, idx) => {
      const val = Number(b.value) || 0;
      const bh = Math.max(8, Math.round((val / maxVal) * chartH));
      const bx = rightBoxX + 24 + spacing + idx * (barW + spacing);
      const by = chartTop + chartH - bh;

      ctx.fillStyle = accent;
      ctx.beginPath();
      ctx.roundRect(bx, by, barW, bh, [4, 4, 0, 0]);
      ctx.fill();

      const valLabel = b.suffix ? `${b.value}${b.suffix}` : String(b.value);
      ctx.fillStyle = '#f8fafc';
      ctx.font = '600 13px "JetBrains Mono", monospace';
      ctx.textAlign = 'center';
      ctx.fillText(valLabel, bx + barW / 2, by - 10);

      ctx.fillStyle = '#94a3b8';
      ctx.font = '500 12px "Inter", sans-serif';
      ctx.fillText(b.label, bx + barW / 2, chartTop + chartH + 24);
      ctx.textAlign = 'left';
    });
  }
}

function wrapCanvasText(ctx, text, x, y, maxWidth, lineHeight) {
  const words = String(text).split(' ');
  let line = '';
  let curY = y;
  for (let n = 0; n < words.length; n++) {
    const testLine = line + words[n] + ' ';
    const metrics = ctx.measureText(testLine);
    if (metrics.width > maxWidth && n > 0) {
      ctx.fillText(line.trim(), x, curY);
      line = words[n] + ' ';
      curY += lineHeight;
    } else {
      line = testLine;
    }
  }
  if (line.trim()) {
    ctx.fillText(line.trim(), x, curY);
  }
}

// ─── Load Sample Deck & Auto-Reset Session ────────────────────────────────
async function loadSampleDeck(deckKey, skipServerReset = false) {
  const normalizedKey = deckKey === 'medtech' ? 'healthcare' : deckKey;
  const deck = SAMPLE_DECKS[normalizedKey];
  if (!deck) return;

  activeDeckKey = normalizedKey;
  slides = deck.map((slide, idx) => ({
    type: 'sample',
    data: slide,
    label: `Slide ${idx + 1} of ${deck.length}`,
  }));
  currentSlide = 0;

  const btnMap = {
    fintech: 'deckBtnFintech',
    healthcare: 'deckBtnHealthcare',
    d2c: 'deckBtnD2c',
  };
  Object.entries(btnMap).forEach(([key, id]) => {
    const btn = document.getElementById(id);
    if (!btn) return;
    if (key === normalizedKey) {
      btn.className = 'px-2.5 py-1.5 rounded text-xs font-medium border transition-colors deck-segment-active';
    } else {
      btn.className = 'px-2.5 py-1.5 rounded text-xs font-medium border transition-colors deck-segment-inactive';
    }
  });

  document.getElementById('slideEmptyState').classList.add('hidden');
  renderCurrentSlide();

  if (!skipServerReset) {
    await resetSession();
  }
}

// ─── File Upload (.pdf, .png, .jpg, .webp) & Auto-Reset ───────────────────
function dataUrlToBlob(dataUrl) {
  const parts = dataUrl.split(',');
  const mimeMatch = parts[0].match(/:(.*?);/);
  const mime = mimeMatch ? mimeMatch[1] : 'image/jpeg';
  const binary = atob(parts[1]);
  const array = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    array[i] = binary.charCodeAt(i);
  }
  return new Blob([array], { type: mime });
}

async function handleFileUpload(event) {
  const files = Array.from(event.target.files || []);
  if (!files.length) return;

  slides = [];
  const indicator = document.getElementById('slideIndicator');
  if (indicator) indicator.textContent = 'Processing deck...';

  ['deckBtnFintech', 'deckBtnHealthcare', 'deckBtnD2c'].forEach((id) => {
    const btn = document.getElementById(id);
    if (btn) {
      btn.className = 'px-2.5 py-1.5 rounded text-xs font-medium border transition-colors deck-segment-inactive';
    }
  });

  for (const file of files) {
    const lowerName = (file.name || '').toLowerCase();
    const isPdf = file.type === 'application/pdf' || lowerName.endsWith('.pdf');
    const isImage =
      file.type.startsWith('image/') || /\.(png|jpe?g|webp)$/i.test(lowerName);

    if (isPdf) {
      await loadPDF(file);
    } else if (isImage) {
      await loadImageDownscaled(file);
    }
  }

  if (slides.length > 0) {
    currentSlide = 0;
    document.getElementById('slideEmptyState').classList.add('hidden');
    renderCurrentSlide();
    await resetSession();
  } else if (indicator) {
    indicator.textContent = 'Slide 0 of 0';
  }

  event.target.value = '';
}

async function loadPDF(file) {
  const arrayBuffer = await file.arrayBuffer();
  if (typeof pdfjsLib !== 'undefined') {
    pdfjsLib.GlobalWorkerOptions.workerSrc =
      'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
  }

  const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
  const pageCount = Math.min(pdf.numPages, MAX_PDF_PAGES);

  for (let i = 1; i <= pageCount; i++) {
    const page = await pdf.getPage(i);
    const baseViewport = page.getViewport({ scale: 1.0 });
    const targetScale = MAX_SLIDE_WIDTH / baseViewport.width;
    const viewport = page.getViewport({ scale: targetScale });

    const offscreen = document.createElement('canvas');
    offscreen.width = Math.round(viewport.width);
    offscreen.height = Math.round(viewport.height);
    const ctx = offscreen.getContext('2d');

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, offscreen.width, offscreen.height);

    await page.render({ canvasContext: ctx, viewport }).promise;

    const dataUrl = offscreen.toDataURL('image/jpeg', JPEG_QUALITY);
    const blob = dataUrlToBlob(dataUrl);
    slides.push({
      type: 'image',
      dataUrl,
      data: blob,
      label: `Slide ${i} of ${pageCount}`,
    });
  }
}

async function loadImageDownscaled(file) {
  return new Promise((resolve) => {
    const img = new Image();
    const objectUrl = URL.createObjectURL(file);

    img.onload = () => {
      const offscreen = document.createElement('canvas');
      let w = img.naturalWidth || img.width;
      let h = img.naturalHeight || img.height;

      if (w > MAX_SLIDE_WIDTH) {
        const ratio = MAX_SLIDE_WIDTH / w;
        w = MAX_SLIDE_WIDTH;
        h = Math.round(h * ratio);
      }

      offscreen.width = w;
      offscreen.height = h;
      const ctx = offscreen.getContext('2d');
      ctx.fillStyle = '#0b0d13';
      ctx.fillRect(0, 0, w, h);
      ctx.drawImage(img, 0, 0, w, h);

      const dataUrl = offscreen.toDataURL('image/jpeg', JPEG_QUALITY);
      const blob = dataUrlToBlob(dataUrl);
      slides.push({
        type: 'image',
        dataUrl,
        data: blob,
        label: `Slide ${slides.length + 1}`,
      });

      URL.revokeObjectURL(objectUrl);
      resolve();
    };

    img.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      resolve();
    };

    img.src = objectUrl;
  });
}

// ─── Slide Navigation & Canvas Rendering ──────────────────────────────────
function renderCurrentSlide() {
  if (slides.length === 0) return;
  const slide = slides[currentSlide];

  if (slide.type === 'sample') {
    drawSlideToCanvas(slide.data);
  } else {
    const canvas = document.getElementById('slideCanvas');
    const ctx = canvas.getContext('2d');
    const W = 1280;
    const H = 720;
    const img = new Image();

    img.onload = () => {
      canvas.width = W;
      canvas.height = H;
      ctx.fillStyle = '#0b0d13';
      ctx.fillRect(0, 0, W, H);
      const scale = Math.min(W / img.width, H / img.height);
      const drawW = Math.round(img.width * scale);
      const drawH = Math.round(img.height * scale);
      ctx.drawImage(
        img,
        Math.round((W - drawW) / 2),
        Math.round((H - drawH) / 2),
        drawW,
        drawH
      );
    };

    if (slide.dataUrl) {
      img.src = slide.dataUrl;
    } else if (slide.data instanceof Blob) {
      const tempUrl = URL.createObjectURL(slide.data);
      const origOnload = img.onload;
      img.onload = () => {
        origOnload();
        URL.revokeObjectURL(tempUrl);
      };
      img.src = tempUrl;
    }
  }

  document.getElementById('slideIndicator').textContent =
    `Slide ${currentSlide + 1} of ${slides.length}`;
}

function prevSlide() {
  if (slides.length === 0) return;
  currentSlide = (currentSlide - 1 + slides.length) % slides.length;
  renderCurrentSlide();
}

function nextSlide() {
  if (slides.length === 0) return;
  currentSlide = (currentSlide + 1) % slides.length;
  renderCurrentSlide();
}

function getSlideBlob() {
  return new Promise((resolve) => {
    const canvas = document.getElementById('slideCanvas');
    if (canvas && typeof canvas.toBlob === 'function') {
      canvas.toBlob(
        (blob) => {
          if (blob) {
            resolve(blob);
            return;
          }
          const slide = slides[currentSlide];
          if (slide && slide.data instanceof Blob) {
            resolve(slide.data);
          } else if (slide && slide.dataUrl) {
            resolve(dataUrlToBlob(slide.dataUrl));
          } else {
            resolve(null);
          }
        },
        'image/jpeg',
        JPEG_QUALITY
      );
      return;
    }
    resolve(null);
  });
}
