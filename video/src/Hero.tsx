import React, { useEffect, useState } from "react";
import {
  AbsoluteFill,
  Img,
  continueRender,
  delayRender,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const IRIS = "#4F46E5";
const INK = "#171A21";
const SANS = "Geist, -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif";
const SERIF = "Fraunces, 'Iowan Old Style', Palatino, Georgia, serif";

// Phase nuit : 0 → 165 (5,5 s) · Phase jour : 165 → 480 (10,5 s)
const NIGHT_END = 165;

const useBrandFonts = () => {
  const [handle] = useState(() => delayRender("fonts"));
  useEffect(() => {
    Promise.all([
      new FontFace("Fraunces", `url(${staticFile("fraunces-var.woff2")})`, {
        weight: "300 700",
      }).load(),
      new FontFace("Geist", `url(${staticFile("geist-var.woff2")})`, {
        weight: "100 900",
      }).load(),
    ])
      .then((fonts) => {
        fonts.forEach((f) => document.fonts.add(f));
        continueRender(handle);
      })
      .catch(() => continueRender(handle));
  }, [handle]);
};

type NightItem = { at: number; time: string; avatar: string; text: React.ReactNode };
const NIGHT_LOG: NightItem[] = [
  {
    at: 18,
    time: "01:40",
    avatar: "raphael@128.webp",
    text: (
      <>
        <b>Raphaël</b> a retouché les 8 photos — lumière, verticales, 3 formats
      </>
    ),
  },
  {
    at: 52,
    time: "02:10",
    avatar: "emma@128.webp",
    text: (
      <>
        <b>Emma</b> a rédigé le texte de l'annonce et tes relances du matin
      </>
    ),
  },
  {
    at: 86,
    time: "03:35",
    avatar: "max@128.webp",
    text: (
      <>
        <b>Max</b> a comparé le bien aux ventes DVF · 2 alertes DPE sur ton secteur
      </>
    ),
  },
  {
    at: 120,
    time: "05:20",
    avatar: "max@128.webp",
    text: (
      <>
        <b>Max</b> a préparé 2 attentions clients — anniversaire, anniversaire d'achat
      </>
    ),
  },
];

type Note = {
  avatar: string;
  name: string;
  role: string;
  text: React.ReactNode;
  from: number;
  to: number;
};

const NOTES: Note[] = [
  {
    avatar: "zoe@128.webp",
    name: "Zoé",
    role: "Community manager · 09:06",
    text: (
      <>
        Le post Facebook &amp; Instagram est <b>prêt à relire</b> — texte d'Emma,
        photos de Raphaël.
      </>
    ),
    from: NIGHT_END + 15,
    to: NIGHT_END + 90,
  },
  {
    avatar: "emma@128.webp",
    name: "Emma",
    role: "Assistante · 09:40",
    text: (
      <>
        2 acquéreurs correspondent à ce bien — <b>proposition de visite</b> samedi
        10 h préparée. Tu valides ?
      </>
    ),
    from: NIGHT_END + 90,
    to: NIGHT_END + 165,
  },
  {
    avatar: "max@128.webp",
    name: "Max",
    role: "WhatsApp · 14:21",
    text: (
      <>
        Rendez-vous déplacé à demain 15 h. <b>Veux-tu que je prépare un SMS</b> pour
        prévenir ton client ?
      </>
    ),
    from: NIGHT_END + 165,
    to: NIGHT_END + 240,
  },
  {
    avatar: "max@128.webp",
    name: "Max",
    role: "Brief du matin · 07:00",
    text: (
      <>
        Ton post a fait <b>47 j'aime</b>, le dossier est <b>complet</b>, tes 3
        relances sont parties.
      </>
    ),
    from: NIGHT_END + 240,
    to: 468,
  },
];

const CHIPS = [
  { avatar: "emma@128.webp", label: "Emma :", strong: "3 relances prêtes", at: NIGHT_END + 20 },
  { avatar: "raphael@128.webp", label: "Raphaël :", strong: "photos prêtes", at: NIGHT_END + 34 },
  { avatar: "zoe@128.webp", label: "Zoé :", strong: "post prêt", at: NIGHT_END + 48 },
];

const NoteCard: React.FC<{ note: Note }> = ({ note }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < note.from || frame > note.to + 12) return null;
  const enter = spring({
    frame: frame - note.from,
    fps,
    config: { damping: 16, stiffness: 130, mass: 0.9 },
  });
  const exit = interpolate(frame, [note.to, note.to + 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute",
        top: 46,
        right: 44,
        width: 400,
        background: "#FFFFFF",
        borderRadius: 16,
        padding: "18px 20px",
        boxShadow: "0 8px 24px rgba(9,11,15,.22), 0 28px 64px rgba(9,11,15,.24)",
        opacity: enter * (1 - exit),
        transform: `translateY(${(1 - enter) * 26 - exit * 18}px) scale(${
          0.96 + enter * 0.04
        })`,
        fontFamily: SANS,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <Img
          src={staticFile(note.avatar)}
          style={{ width: 42, height: 42, borderRadius: "50%" }}
        />
        <div>
          <div style={{ fontSize: 16.5, fontWeight: 650, color: INK }}>
            {note.name}
          </div>
          <div style={{ fontSize: 12.5, color: "#8B91A3" }}>{note.role}</div>
        </div>
        <div
          style={{
            marginLeft: "auto",
            width: 9,
            height: 9,
            borderRadius: "50%",
            background: "#12B76A",
          }}
        />
      </div>
      <div style={{ marginTop: 12, fontSize: 16, lineHeight: 1.5, color: INK }}>
        {note.text}
      </div>
    </div>
  );
};

export const Hero: React.FC = () => {
  useBrandFonts();
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const zoom = interpolate(
    frame,
    [0, durationInFrames / 2, durationInFrames],
    [1.03, 1.08, 1.03]
  );
  // Voile de nuit : présent au début, se lève à l'aube (NIGHT_END), revient à la toute fin pour la boucle.
  const nightVeil = interpolate(
    frame,
    [0, NIGHT_END - 25, NIGHT_END, durationInFrames - 14, durationInFrames],
    [1, 1, 0, 0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const clockTime =
    frame < 45 ? "01:40" : frame < 82 ? "02:10" : frame < 116 ? "03:35" : frame < 148 ? "05:20" : "06:55";

  return (
    <AbsoluteFill style={{ background: "#090B0F", overflow: "hidden" }}>
      <Img
        src={staticFile("villa_hero.jpg")}
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${zoom})`,
        }}
      />
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to top, rgba(10,18,28,.94) 0%, rgba(13,24,38,.5) 46%, rgba(15,30,48,.12) 72%, rgba(18,34,54,.4) 100%)",
        }}
      />
      {/* Voile de nuit */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to bottom, rgba(6,9,18,.9) 0%, rgba(8,11,22,.82) 55%, rgba(10,14,26,.9) 100%)",
          opacity: nightVeil,
        }}
      />

      {/* Badge priorité (jour) */}
      <div
        style={{
          position: "absolute",
          top: 26,
          left: 30,
          display: "flex",
          alignItems: "center",
          gap: 8,
          background: IRIS,
          color: "#fff",
          fontFamily: SANS,
          fontSize: 13,
          fontWeight: 650,
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          padding: "8px 14px",
          borderRadius: 9,
          opacity: 1 - nightVeil,
        }}
      >
        <div
          style={{
            width: 7,
            height: 7,
            borderRadius: "50%",
            background: "#fff",
            opacity: 0.5 + 0.5 * Math.abs(Math.sin(frame / 14)),
          }}
        />
        À traiter en priorité
      </div>

      {/* Horloge + titre de nuit */}
      <div
        style={{
          position: "absolute",
          top: 34,
          left: 34,
          fontFamily: SANS,
          color: "#fff",
          opacity: nightVeil,
        }}
      >
        <div
          style={{
            fontSize: 13,
            fontWeight: 650,
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            color: "#A5B4FC",
          }}
        >
          Pendant que tu dors
        </div>
        <div
          style={{
            fontVariantNumeric: "tabular-nums",
            fontFamily: SERIF,
            fontSize: 66,
            lineHeight: 1,
            marginTop: 10,
            letterSpacing: "-0.01em",
          }}
        >
          {clockTime}
        </div>
        <div style={{ fontSize: 15, marginTop: 8, color: "rgba(255,255,255,.72)" }}>
          ton équipe travaille
        </div>
      </div>

      {/* Log de nuit */}
      <div
        style={{
          position: "absolute",
          right: 44,
          top: 46,
          width: 430,
          display: "flex",
          flexDirection: "column",
          gap: 10,
          fontFamily: SANS,
          opacity: nightVeil,
        }}
      >
        {NIGHT_LOG.map((n) => {
          const s = spring({
            frame: frame - n.at,
            fps,
            config: { damping: 15, stiffness: 120 },
          });
          return (
            <div
              key={n.time}
              style={{
                display: "flex",
                gap: 11,
                alignItems: "flex-start",
                background: "rgba(20,24,34,.86)",
                border: "0.5px solid rgba(242,243,247,.16)",
                borderRadius: 13,
                padding: "12px 15px",
                color: "rgba(242,243,247,.9)",
                fontSize: 14.5,
                lineHeight: 1.45,
                opacity: s,
                transform: `translateY(${(1 - s) * 18}px)`,
              }}
            >
              <span
                style={{
                  color: "#A5B4FC",
                  fontWeight: 650,
                  fontVariantNumeric: "tabular-nums",
                  flex: "none",
                  paddingTop: 1,
                }}
              >
                {n.time}
              </span>
              <Img
                src={staticFile(n.avatar)}
                style={{ width: 26, height: 26, borderRadius: "50%", flex: "none" }}
              />
              <span>{n.text}</span>
            </div>
          );
        })}
      </div>

      {/* Identité du bien (jour) */}
      <div
        style={{
          position: "absolute",
          left: 34,
          bottom: 104,
          color: "#fff",
          fontFamily: SANS,
          opacity: 1 - nightVeil,
        }}
      >
        <div
          style={{
            fontSize: 13,
            fontWeight: 650,
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            color: "rgba(255,255,255,.66)",
          }}
        >
          Le bien qui bouge ce matin
        </div>
        <div
          style={{
            fontFamily: SERIF,
            fontSize: 40,
            lineHeight: 1.12,
            marginTop: 8,
            letterSpacing: "-0.02em",
            fontWeight: 450,
          }}
        >
          Villa des Cèdres — Aix-en-Provence
        </div>
        <div style={{ marginTop: 8, fontSize: 17, color: "rgba(255,255,255,.8)" }}>
          <span style={{ fontSize: 25, fontWeight: 550, color: "#fff" }}>
            875 000 €
          </span>
          {"   "}· Villa · 210 m² · 6 pièces · piscine · mandat exclusif
        </div>
      </div>

      {/* Chips agents (jour) */}
      <div
        style={{
          position: "absolute",
          left: 34,
          bottom: 32,
          display: "flex",
          gap: 10,
          fontFamily: SANS,
          opacity: 1 - nightVeil,
        }}
      >
        {CHIPS.map((c) => {
          const s = spring({
            frame: frame - c.at,
            fps,
            config: { damping: 15, stiffness: 140 },
          });
          return (
            <div
              key={c.avatar + c.strong}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 9,
                padding: "9px 15px 9px 10px",
                borderRadius: 11,
                background: "rgba(255,255,255,.13)",
                border: "0.5px solid rgba(255,255,255,.22)",
                backdropFilter: "blur(10px)",
                color: "rgba(255,255,255,.94)",
                fontSize: 15,
                opacity: s,
                transform: `translateY(${(1 - s) * 14}px)`,
              }}
            >
              <Img
                src={staticFile(c.avatar)}
                style={{ width: 27, height: 27, borderRadius: "50%" }}
              />
              {c.label} <b style={{ color: "#fff" }}>{c.strong}</b>
            </div>
          );
        })}
      </div>

      {NOTES.map((n) => (
        <NoteCard key={n.role} note={n} />
      ))}
    </AbsoluteFill>
  );
};
