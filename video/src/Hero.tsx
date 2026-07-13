import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const IRIS = "#4F46E5";
const INK = "#171A21";
const SANS =
  "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', sans-serif";
const SERIF = "'Iowan Old Style', 'Palatino Linotype', Palatino, Georgia, serif";

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
    role: "Réseaux sociaux · à l'instant",
    text: (
      <>
        Nouveau mandat détecté — le post Facebook &amp; Instagram est{" "}
        <b>prêt à relire</b>, avec les 8 photos.
      </>
    ),
    from: 15,
    to: 100,
  },
  {
    avatar: "emma@128.webp",
    name: "Emma",
    role: "Assistante · 09:40",
    text: (
      <>
        2 acquéreurs correspondent à ce bien — <b>proposition de visite</b>{" "}
        samedi 10 h préparée. Tu valides ?
      </>
    ),
    from: 100,
    to: 185,
  },
  {
    avatar: "christine@128.webp",
    name: "Christine",
    role: "Juridique · 11:30",
    text: (
      <>
        DPE manquant au dossier — le <b>mail au vendeur</b> est en brouillon
        dans ta boîte.
      </>
    ),
    from: 185,
    to: 270,
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
    from: 270,
    to: 352,
  },
];

const CHIPS = [
  { avatar: "emma@128.webp", label: "Emma :", strong: "3 relances prêtes", at: 26 },
  { avatar: "christine@128.webp", label: "Christine :", strong: "DPE manquant", at: 40 },
  { avatar: "zoe@128.webp", label: "Zoé :", strong: "post prêt", at: 54 },
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
      <div
        style={{
          marginTop: 12,
          fontSize: 16,
          lineHeight: 1.5,
          color: INK,
        }}
      >
        {note.text}
      </div>
    </div>
  );
};

export const Hero: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  // Ken Burns aller-retour → boucle sans couture.
  const zoom = interpolate(
    frame,
    [0, durationInFrames / 2, durationInFrames],
    [1.03, 1.08, 1.03]
  );
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

      {/* Badge priorité */}
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

      {/* Identité du bien */}
      <div
        style={{
          position: "absolute",
          left: 34,
          bottom: 104,
          color: "#fff",
          fontFamily: SANS,
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

      {/* Chips agents */}
      <div
        style={{
          position: "absolute",
          left: 34,
          bottom: 32,
          display: "flex",
          gap: 10,
          fontFamily: SANS,
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
        <NoteCard key={n.name} note={n} />
      ))}
    </AbsoluteFill>
  );
};
