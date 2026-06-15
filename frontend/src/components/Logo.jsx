import { Link } from "react-router";

export const Logo = ({ className = "" }) => {
  return (
      <h1
        className={`font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent ${className}`}
        style={{ backgroundImage: "var(--gradient-brand)" }}
      >
        FuldaNexus
      </h1>
  );
};
