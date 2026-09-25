using System;
using System.Collections.Generic;

namespace Beispiel.Fahrtenbuch
{
    /// <summary>
    /// Berechnet die Kosten der Fahrten eines Fahrzeugs.
    /// </summary>
    public sealed class FahrtRechner
    {
        private const decimal SatzProKilometer = 0.30m;
        private readonly IReadOnlyList<Fahrt> fahrten;

        public FahrtRechner(IReadOnlyList<Fahrt> fahrten)
        {
            // Guard: ohne Fahrten gibt es nichts zu rechnen
            if (null == fahrten)
                throw new ArgumentNullException(nameof(fahrten));

            this.fahrten = fahrten;
        }

        public decimal Summe(string kennzeichen, bool nurPrivat = false)
        {
            var summe = 0m;
            foreach (var fahrt in this.fahrten)
            {
                if (!string.Equals(fahrt.Kennzeichen, kennzeichen, StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }

                summe += fahrt.Kilometer * SatzProKilometer;
            }

            return summe > 0 ? summe : 0m;
        }
    }
}
