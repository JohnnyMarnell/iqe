Prompt:

**IMPORTANT**: I want one artifact generated, a full python script cuts.py that I can run, achieving the below on an input video.

Ultrathink. Our challenge is to determine clip transitions in a long (1 hour) video. The long video is made up of clips sequentially, each an animation used for a DJ / VJ / music visualization experience (no audio in full video however). There are no kinds of transition effects between them in the long video, they are a sudden jump to the next animation in the sequence.

Oftentimes the sub-clips are of a similar color palette within the full (e.g. synthwave pinks and blues throughout).

Deep research the best way to solve this problem, available free tools, papers, and scripts published.

Come up with a Python implementation that will both generate JSON describing transitions detected (exact frame or millisecond precision please), and a mode where it parses that and quickly splits lossless-ly with ffmpeg.

Maximizing sub-clip length is great, as it means I get to present longer animations, HOWEVER err on the side of safety. Showing even one frame from another clip together would be disastrous and jarring.

I’d rather you come up with and explore ideas, but some of mine, if they help:

- maybe grayscale filtering pre transform could help? (There’s a lot of black in some, for starters. Maybe a tolerance of black and non black bucketing then detecting motion jumps too large could help?)
- color palettes maybe similar, so hue averaging and analyzing might not work as well
- would downscaling resolution or up sampling frame rate help or hurt or not matter?
- multi pass and multi algorithm combination of process?

Other notes:
1. In most cases, there is not gradual transitions, they jump cut to the next, completely separate scene, no cross fade or anything. Much of the different sub clips are still similar colors
2. Accuracy is paramount, processing speed doesn’t matter
3. I can give you a sample YouTube link you’ll probably complain you can’t watch : https://www.youtube.com/watch?v=K3-m4Gf6_bw
4. I'll attach here a left to right, top to bottom image export of tiled thumbnails, showing one transition