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

// 480 frames @30fps = 16 s : une journée complète 07:00 → 07:00.
// Le jour domine (07:00→19:00 sur 0→290), la nuit passe vite (290→436),
// finale « Six agents. 24 h/24. » (436→476), boucle propre à 480.
const FINALE_IN = 436;
const FINALE_OUT = 474;

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

// Horloge continue : paires [frame, heure décimale] (heures > 24 = lendemain).
const CLOCK_FRAMES = [0, 12, 52, 94, 140, 186, 232, 290, 344, 390, 424, 448, 480];
const CLOCK_HOURS = [7, 7.1, 9.2, 11.68, 14.33, 16, 18, 22.78, 25.67, 29.33, 30.6, 31, 31];

const fmtClock = (h: number) => {
  const hh = Math.floor(h) % 24;
  const mm = Math.floor((h % 1) * 60);
  return `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}`;
};

type Note = {
  avatar: string;
  name: string;
  role: string;
  text: React.ReactNode;
  from: number;
  to: number;
};

// Contenus adossés au réel (data/agents.json / annexe A du spec).
const NOTES: Note[] = [
  {
    avatar: "max@128.webp",
    name: "Max",
    role: "Brief du matin · 07:00",
    text: (
      <>
        Deux visites aujourd'hui (<b>10 h</b> Bihorel, <b>15 h</b> rive droite),
        trois emails importants triés — et <b>deux DPE tout frais</b> dans ton
        secteur.
      </>
    ),
    from: 8,
    to: 48,
  },
  {
    avatar: "emma@128.webp",
    name: "Emma",
    role: "Assistante · 09:12",
    text: (
      <>
        Brouillon de réponse <b>prêt</b> pour M. Moreau — tu relis, tu ajustes,
        tu envoies.
      </>
    ),
    from: 54,
    to: 90,
  },
  {
    avatar: "emma@128.webp",
    name: "Emma",
    role: "Assistante · 11:41",
    text: (
      <>
        Visite de samedi <b>11 h confirmée</b> — c'est dans ton agenda.
      </>
    ),
    from: 96,
    to: 134,
  },
  {
    avatar: "max@128.webp",
    name: "Max",
    role: "WhatsApp · 14:20",
    text: (
      <>
        Vocal reçu : « déplace mon rdv de 14 h ». <b>Fait</b> — demain 15 h,
        client prévenu après ta validation.
      </>
    ),
    from: 142,
    to: 182,
  },
  {
    avatar: "lucas@128.webp",
    name: "Lucas",
    role: "Estimation · 16:00",
    text: (
      <>
        Rapport de marché <b>prêt</b> pour ton rendez-vous — douze ventes
        comparables, à ta marque.
      </>
    ),
    from: 188,
    to: 228,
  },
  {
    avatar: "zoe@128.webp",
    name: "Zoé",
    role: "Community manager · 18:00",
    text: (
      <>
        Le post de l'exclusivité est <b>parti</b> — visuel à ta charte, Instagram
        &amp; Facebook.
      </>
    ),
    from: 234,
    to: 274,
  },
  {
    avatar: "emma@128.webp",
    name: "Emma",
    role: "Assistante · 22:47",
    text: (
      <>
        Un vendeur a écrit à 22 h 41 — <b>brouillon de réponse prêt</b> pour
        demain matin.
      </>
    ),
    from: 292,
    to: 330,
  },
  {
    avatar: "raphael@128.webp",
    name: "Raphaël",
    role: "Photographe · 01:40",
    text: (
      <>
        <b>18 photos retouchées</b> — lumière, verticales, home staging du
        salon vide.
      </>
    ),
    from: 340,
    to: 378,
  },
  {
    avatar: "max@128.webp",
    name: "Max",
    role: "Coordination · 05:20",
    text: (
      <>
        Modelo synchronisé, fiches à jour — <b>ton brief de 7 h est prêt</b>.
      </>
    ),
    from: 386,
    to: 422,
  },
];

const AVATARS = [
  "max@128.webp",
  "emma@128.webp",
  "christine@128.webp",
  "zoe@128.webp",
  "raphael@128.webp",
  "lucas@128.webp",
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

  const hour = interpolate(frame, CLOCK_FRAMES, CLOCK_HOURS, {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const clock = fmtClock(hour);
  const isNight = hour % 24 >= 20.5 || hour % 24 < 6.3;

  // Voile de nuit LÉGER (le jour domine, la nuit passe vite) : monte vers 21 h,
  // se lève à l'aube (~06:20). Jamais aussi sombre que l'ancienne version.
  const hNorm = hour; // 7 → 31
  const nightVeil = interpolate(
    hNorm,
    [19.5, 21.5, 28.5, 30.3],
    [0, 0.72, 0.72, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Finale : « Six agents. 24 h/24. »
  const finaleIn = spring({
    frame: frame - FINALE_IN,
    fps,
    config: { damping: 16, stiffness: 110 },
  });
  const finaleOut = interpolate(frame, [FINALE_OUT, durationInFrames - 2], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const finaleOpacity = frame < FINALE_IN ? 0 : finaleIn * (1 - finaleOut);

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
      {/* Voile de nuit (léger) */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to bottom, rgba(6,9,18,.9) 0%, rgba(8,11,22,.8) 55%, rgba(10,14,26,.9) 100%)",
          opacity: nightVeil,
        }}
      />

      {/* Horloge continue 07:00 → 07:00 */}
      <div
        style={{
          position: "absolute",
          top: 34,
          left: 34,
          fontFamily: SANS,
          color: "#fff",
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
          Une journée avec ton équipe
        </div>
        <div
          style={{
            fontVariantNumeric: "tabular-nums",
            fontFamily: SERIF,
            fontSize: 66,
            lineHeight: 1,
            marginTop: 10,
            letterSpacing: "-0.01em",
            textShadow: "0 2px 18px rgba(9,11,15,.45)",
          }}
        >
          {clock}
        </div>
        <div style={{ fontSize: 15, marginTop: 8, color: "rgba(255,255,255,.75)" }}>
          {isNight ? "ton équipe travaille encore" : "ton équipe est au travail"}
        </div>
      </div>

      {/* Identité du bien (jour uniquement) */}
      <div
        style={{
          position: "absolute",
          left: 34,
          bottom: 32,
          color: "#fff",
          fontFamily: SANS,
          opacity: (1 - nightVeil) * (1 - finaleOpacity),
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
          Mandat exclusif
        </div>
        <div
          style={{
            fontFamily: SERIF,
            fontSize: 36,
            lineHeight: 1.12,
            marginTop: 8,
            letterSpacing: "-0.02em",
            fontWeight: 450,
          }}
        >
          Villa des Cèdres — Aix-en-Provence
        </div>
        <div style={{ marginTop: 6, fontSize: 16, color: "rgba(255,255,255,.8)" }}>
          <span style={{ fontSize: 23, fontWeight: 550, color: "#fff" }}>
            875 000 €
          </span>
          {"  "}· Villa · 210 m² · 6 pièces · piscine
        </div>
      </div>

      {/* Notifications de la journée */}
      {NOTES.map((n) => (
        <NoteCard key={n.role} note={n} />
      ))}

      {/* Finale : Six agents. 24 h/24. */}
      <AbsoluteFill
        style={{
          background: "rgba(9,11,15,.78)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          opacity: finaleOpacity,
        }}
      >
        <div style={{ textAlign: "center", fontFamily: SANS, color: "#fff" }}>
          <div style={{ display: "flex", justifyContent: "center" }}>
            {AVATARS.map((a, i) => (
              <Img
                key={a}
                src={staticFile(a)}
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: "50%",
                  border: "2.5px solid rgba(255,255,255,.9)",
                  marginLeft: i === 0 ? 0 : -14,
                  transform: `translateY(${
                    (1 -
                      spring({
                        frame: frame - FINALE_IN - i * 3,
                        fps,
                        config: { damping: 14, stiffness: 140 },
                      })) *
                    16
                  }px)`,
                }}
              />
            ))}
          </div>
          <div
            style={{
              fontFamily: SERIF,
              fontSize: 54,
              letterSpacing: "-0.015em",
              marginTop: 22,
              fontWeight: 480,
            }}
          >
            Six agents. 24 h/24.
          </div>
          <div style={{ marginTop: 10, fontSize: 17, color: "#A5B4FC" }}>
            Toi, tu fais visiter et tu signes.
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
