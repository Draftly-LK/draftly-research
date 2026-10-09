import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';

// Verified against frontend/src/styles/globals.css and the current BrandMark.
export const palette = {navy: '#0F1F38', ink: '#0F1B2E', gold: '#C69436', paper: '#F3F5F8', cream: '#F9E8C6', muted: '#A7B3C2'};
export const type = {ui: 'FilmPlex, Arial, sans-serif', display: 'Georgia, serif'};
export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export const FilmBase: React.FC<{children: React.ReactNode}> = ({children}) => <AbsoluteFill style={{background: palette.navy, color: palette.paper, fontFamily: type.ui, overflow: 'hidden'}}>
  <style>{`@font-face {font-family: FilmPlex; src: url('${staticFile('brand/plex-latin.woff2')}') format('woff2'); font-weight: 100 900;} * {box-sizing: border-box;}`}</style>
  {children}
</AbsoluteFill>;

export const Stamp: React.FC<{text: string; dark?: boolean}> = ({text, dark}) => <div style={{position: 'absolute', left: 96, top: 58, color: dark ? palette.ink : palette.cream, fontSize: 23, letterSpacing: 2, textTransform: 'uppercase', zIndex: 8}}>{text}</div>;

export const BrandBug: React.FC = () => <Img src={staticFile('brand/logo-mark-white.png')} style={{position: 'absolute', right: 96, top: 48, width: 58, height: 58, zIndex: 9}}/>;

export const Note: React.FC<{children: React.ReactNode; dark?: boolean}> = ({children, dark}) => <div style={{position: 'absolute', left: 96, right: 96, bottom: 66, color: dark ? palette.ink : palette.cream, fontSize: 28, lineHeight: 1.4, zIndex: 8}}>{children}</div>;

export const Desk: React.FC = () => <AbsoluteFill style={{background: '#57483D'}}>
  <svg width="1920" height="1080" viewBox="0 0 1920 1080" style={{position: 'absolute'}}>
    <defs><pattern id="wood" width="460" height="1080" patternUnits="userSpaceOnUse"><rect width="460" height="1080" fill="#57483D"/><path d="M20 0 C38 240 -10 660 20 1080 M65 0 C48 300 86 660 65 1080 M350 0 C318 380 395 860 350 1080 M440 0 L440 1080" fill="none" stroke="#6B5C4C" strokeWidth="3" opacity=".3"/></pattern></defs>
    <rect width="1920" height="1080" fill="url(#wood)"/>
  </svg>
  <div style={{position:'absolute',inset:0,boxShadow:'inset 0 0 180px rgba(15,27,46,.45)'}}/>
</AbsoluteFill>;

export const SourcePage: React.FC<{id: string; style?: React.CSSProperties}> = ({id, style}) => <Img src={staticFile(`evidence/${id}.png`)} style={{display: 'block', boxShadow: '0 16px 36px rgba(0,0,0,.22)', ...style}}/>;
