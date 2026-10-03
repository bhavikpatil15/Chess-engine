// pieces.js - Embedded clean vector SVG Staunton pieces
// Self-contained, scalable, and crisp on any display

const PIECE_SVGS = {
  // White King
  'K': `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45" width="100%" height="100%">
    <g fill="none" fill-rule="evenodd" stroke="#1c1917" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M22.5 11.63V6M20 8h5" stroke-linejoin="miter"/>
      <path d="M22.5 25s4.5-7.5 3-10.5c0 0-1-2.5-3-2.5s-3 2.5-3 2.5c-1.5 3 3 10.5 3 10.5" fill="#f8fafc" stroke-linecap="butt"/>
      <path d="M11.5 37c5.5 3.5 15.5 3.5 21 0v-7s9-4.5 6-10.5c-4-6.5-13.5-3.5-16 4V23c-2.5-7.5-12-10.5-16-4-3 6 6 10.5 6 10.5v7z" fill="#f8fafc"/>
      <path d="M11.5 30c5.5-3 15.5-3 21 0m-21 3.5c5.5-3 15.5-3 21 0m-21 3.5c5.5-3 15.5-3 21 0"/>
    </g>
  </svg>`,

  // White Queen
  'Q': `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45" width="100%" height="100%">
    <g fill="#f8fafc" fill-rule="evenodd" stroke="#1c1917" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M9 26c8.5-1.5 21-1.5 27 0l2-12-7 11V11l-5.5 13.5-3-15-3 15-5.5-13.5V25l-7-11 2 12z"/>
      <path d="M9 26c0 2 1.5 2 2.5 4 1 1.5 1 1 .5 3.5-1.5 1-1.5 2.5-1.5 2.5-1.5 1.5.5 2.5.5 2.5 6.5 1 16.5 1 23 0 0 0 2-1 .5-2.5 0 0 0-1.5-1.5-2.5-.5-2.5-.5-2 .5-3.5 1-2 2.5-2 2.5-4-8.5-1.5-18.5-1.5-27 0z"/>
      <path d="M11 38.5a35 35 1 0 0 23 0" fill="none" stroke-linecap="butt"/>
      <circle cx="6" cy="12" r="2"/>
      <circle cx="14" cy="9" r="2"/>
      <circle cx="22.5" cy="8" r="2"/>
      <circle cx="31" cy="9" r="2"/>
      <circle cx="39" cy="12" r="2"/>
    </g>
  </svg>`,

  // White Rook
  'R': `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45" width="100%" height="100%">
    <g fill="#f8fafc" fill-rule="evenodd" stroke="#1c1917" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M9 39h27v-3H9v3zm3-3v-4.5h21V36H12zm2-4.5l1.5-16.5h14L31 31.5H14zM11 14h23v-5H11v5z"/>
      <path d="M12 9V6h3v3h5V6h5v3h5V6h3v3"/>
      <path d="M14 29.5h17m-18-6h19m-17-6h15" fill="none" stroke-linejoin="miter"/>
    </g>
  </svg>`,

  // White Bishop
  'B': `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45" width="100%" height="100%">
    <g fill="none" fill-rule="evenodd" stroke="#1c1917" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <g fill="#f8fafc" stroke-linecap="butt">
        <path d="M9 36c3.39-.97 10.11.43 13.5-2 3.39 2.43 10.11 1.03 13.5 2 0 0 1.65.54 3 2-.68.97-1.65.99-3 .5-3.39-.97-10.11.46-13.5-1-3.39 1.46-10.11.03-13.5 1-1.35.49-2.32.47-3-.5 1.35-1.46 3-2 3-2z"/>
        <path d="M15 32c2.5 2.5 12.5 2.5 15 0 .5-1.5 0-2 0-2 0-2.5-2.5-4-2.5-4 5.5-1.5 6-11.5-5-15.5-11 4-10.5 14-5 15.5 0 0-2.5 1.5-2.5 4 0 0-.5.5 0 2z"/>
        <circle cx="22.5" cy="8" r="1.5"/>
      </g>
      <path d="M25 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 1 1 5 0z" fill="#f8fafc"/>
      <path d="M17.5 26h10M15 30h15m-7.5-14.5v5m-3-2.5h6" stroke-linejoin="miter"/>
    </g>
  </svg>`,

  // White Knight
  'N': `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45" width="100%" height="100%">
    <g fill="none" fill-rule="evenodd" stroke="#1c1917" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M22 10c10.5 1 16.5 8 16 29H15c0-9 10-6.5 8-21" fill="#f8fafc"/>
      <path d="M24 18c.38 2.91-5.55 7.37-8 9-3 2-2.82 4.34-5 4-1.042-.94 1.41-3.04 0-3-1 0-.06 1.09-1 2-1 1-2 2-3.5 1-2-1.5-3.5-3-1.5-6 1.83-2.74 6.72-3.79 9-4.5 2-.63 6.13-.88 6.5-2.5z" fill="#f8fafc"/>
      <path d="M9.5 25.5a.5.5 0 1 1-1 0 .5.5 0 1 1 1 0z" fill="#1c1917"/>
      <path d="M15 15.5a.5.5 0 1 1-1 0 .5.5 0 1 1 1 0z" fill="#1c1917"/>
    </g>
  </svg>`,

  // White Pawn
  'P': `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45" width="100%" height="100%">
    <path d="M22.5 9c-2.21 0-4 1.79-4 4 0 .89.29 1.71.78 2.38C17.33 16.5 16 18.59 16 21c0 2.03.94 3.84 2.41 5.03-3 1.06-7.41 5.55-7.41 13.47h23c0-7.92-4.41-12.41-7.41-13.47 1.47-1.19 2.41-3 2.41-5.03 0-2.41-1.33-4.5-3.28-5.62.49-.67.78-1.49.78-2.38 0-2.21-1.79-4-4-4z" fill="#f8fafc" stroke="#1c1917" stroke-width="1.5" stroke-linecap="round"/>
  </svg>`,

  // Black King
  'k': `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45" width="100%" height="100%">
    <g fill="none" fill-rule="evenodd" stroke="#f8fafc" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M22.5 11.63V6M20 8h5" stroke-linejoin="miter"/>
      <path d="M22.5 25s4.5-7.5 3-10.5c0 0-1-2.5-3-2.5s-3 2.5-3 2.5c-1.5 3 3 10.5 3 10.5" fill="#1e293b" stroke-linecap="butt"/>
      <path d="M11.5 37c5.5 3.5 15.5 3.5 21 0v-7s9-4.5 6-10.5c-4-6.5-13.5-3.5-16 4V23c-2.5-7.5-12-10.5-16-4-3 6 6 10.5 6 10.5v7z" fill="#1e293b"/>
      <path d="M11.5 30c5.5-3 15.5-3 21 0m-21 3.5c5.5-3 15.5-3 21 0m-21 3.5c5.5-3 15.5-3 21 0" stroke="#f8fafc"/>
    </g>
  </svg>`,

  // Black Queen
  'q': `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45" width="100%" height="100%">
    <g fill="#1e293b" fill-rule="evenodd" stroke="#f8fafc" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M9 26c8.5-1.5 21-1.5 27 0l2-12-7 11V11l-5.5 13.5-3-15-3 15-5.5-13.5V25l-7-11 2 12z"/>
      <path d="M9 26c0 2 1.5 2 2.5 4 1 1.5 1 1 .5 3.5-1.5 1-1.5 2.5-1.5 2.5-1.5 1.5.5 2.5.5 2.5 6.5 1 16.5 1 23 0 0 0 2-1 .5-2.5 0 0 0-1.5-1.5-2.5-.5-2.5-.5-2 .5-3.5 1-2 2.5-2 2.5-4-8.5-1.5-18.5-1.5-27 0z"/>
      <path d="M11 38.5a35 35 1 0 0 23 0" fill="none" stroke-linecap="butt"/>
      <circle cx="6" cy="12" r="2" fill="#f8fafc"/>
      <circle cx="14" cy="9" r="2" fill="#f8fafc"/>
      <circle cx="22.5" cy="8" r="2" fill="#f8fafc"/>
      <circle cx="31" cy="9" r="2" fill="#f8fafc"/>
      <circle cx="39" cy="12" r="2" fill="#f8fafc"/>
    </g>
  </svg>`,

  // Black Rook
  'r': `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45" width="100%" height="100%">
    <g fill="#1e293b" fill-rule="evenodd" stroke="#f8fafc" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M9 39h27v-3H9v3zm3-3v-4.5h21V36H12zm2-4.5l1.5-16.5h14L31 31.5H14zM11 14h23v-5H11v5z"/>
      <path d="M12 9V6h3v3h5V6h5v3h5V6h3v3"/>
      <path d="M14 29.5h17m-18-6h19m-17-6h15" fill="none" stroke-linejoin="miter"/>
    </g>
  </svg>`,

  // Black Bishop
  'b': `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45" width="100%" height="100%">
    <g fill="none" fill-rule="evenodd" stroke="#f8fafc" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <g fill="#1e293b" stroke-linecap="butt">
        <path d="M9 36c3.39-.97 10.11.43 13.5-2 3.39 2.43 10.11 1.03 13.5 2 0 0 1.65.54 3 2-.68.97-1.65.99-3 .5-3.39-.97-10.11.46-13.5-1-3.39 1.46-10.11.03-13.5 1-1.35.49-2.32.47-3-.5 1.35-1.46 3-2 3-2z"/>
        <path d="M15 32c2.5 2.5 12.5 2.5 15 0 .5-1.5 0-2 0-2 0-2.5-2.5-4-2.5-4 5.5-1.5 6-11.5-5-15.5-11 4-10.5 14-5 15.5 0 0-2.5 1.5-2.5 4 0 0-.5.5 0 2z"/>
        <circle cx="22.5" cy="8" r="1.5"/>
      </g>
      <path d="M25 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 1 1 5 0z" fill="#1e293b"/>
      <path d="M17.5 26h10M15 30h15m-7.5-14.5v5m-3-2.5h6" stroke-linejoin="miter"/>
    </g>
  </svg>`,

  // Black Knight
  'n': `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45" width="100%" height="100%">
    <g fill="none" fill-rule="evenodd" stroke="#f8fafc" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M22 10c10.5 1 16.5 8 16 29H15c0-9 10-6.5 8-21" fill="#1e293b"/>
      <path d="M24 18c.38 2.91-5.55 7.37-8 9-3 2-2.82 4.34-5 4-1.042-.94 1.41-3.04 0-3-1 0-.06 1.09-1 2-1 1-2 2-3.5 1-2-1.5-3.5-3-1.5-6 1.83-2.74 6.72-3.79 9-4.5 2-.63 6.13-.88 6.5-2.5z" fill="#1e293b"/>
      <path d="M9.5 25.5a.5.5 0 1 1-1 0 .5.5 0 1 1 1 0z" fill="#f8fafc"/>
      <path d="M15 15.5a.5.5 0 1 1-1 0 .5.5 0 1 1 1 0z" fill="#f8fafc"/>
    </g>
  </svg>`,

  // Black Pawn
  'p': `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45" width="100%" height="100%">
    <path d="M22.5 9c-2.21 0-4 1.79-4 4 0 .89.29 1.71.78 2.38C17.33 16.5 16 18.59 16 21c0 2.03.94 3.84 2.41 5.03-3 1.06-7.41 5.55-7.41 13.47h23c0-7.92-4.41-12.41-7.41-13.47 1.47-1.19 2.41-3 2.41-5.03 0-2.41-1.33-4.5-3.28-5.62.49-.67.78-1.49.78-2.38 0-2.21-1.79-4-4-4z" fill="#1e293b" stroke="#f8fafc" stroke-width="1.5" stroke-linecap="round"/>
  </svg>`
};
