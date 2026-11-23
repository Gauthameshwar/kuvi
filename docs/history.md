# Design history

| Snapshot | Main change |
|---|---|
| [Initial concept](../revisions/01-concept/) | Three-piece head, preliminary component layout and many fasteners. |
| [Serviceable enclosure](../revisions/02-serviceable/) | Two casing halves, separately installed battery tray and screwless speaker keeper. |
| [Print-test model](../revisions/03-print-test/) | Measured components, internal rear USB, simpler vibrator fastening, guided ear buttons and corrected assembly clearances. |

Between the serviceable enclosure and the current model, the USB connection moved from underneath to the rear using a short ribbon extension. The base became broader and more stable. Caliper measurements replaced estimates, the battery gained a third mounting point, and the speaker grille followed the reference design.

The raised vibrator sled was replaced by a bottom slide-in bed with a single internal screw. Later changes improved the speaker fit, rounded battery mounting tabs and replaced plain button caps with sculpted bun ears. The final alignment lip is straight so it can enter the rear casing without catching. The print-test revision later replaced the trapped speaker keeper and its thin latch slots with a straight insert-fit pocket and rounded lead notch.

The saved snapshots use static solids. Their `model.py` helpers open and inspect the embedded geometry; the active helper also constructs the current geometry from the shared CSV. Historical generators and intermediate checkpoints are not part of the public working tree. The current generator remains under `scripts/`.
