# Notes / Scratchity Scratchy Scratch-Scratch


JSON to add a bunch of modulators (copied field lines in AudioModulators.java)
```shell
id=56972; for mod in $(pbpaste | acut -f 3 | xargs) ; do node -e "console.log(JSON.stringify({ id:$id, class: 'org.iqe.AudioModulators\$$mod', parameters: { running: true} , internal: { modulationColor: 0, modulationControlsExpanded: false } }) + ',')" ; id=$(($id + 1)) ; done | tee /dev/stderr | pbcopy


{"id":56972,"class":"org.iqe.AudioModulators$Boots","parameters":{"running":true},"internal":{"modulationColor":0,"modulationControlsExpanded":false}},
{"id":56973,"class":"org.iqe.AudioModulators$Quarter","parameters":{"running":true},"internal":{"modulationColor":0,"modulationControlsExpanded":false}},
{"id":56974,"class":"org.iqe.AudioModulators$Bar","parameters":{"running":true},"internal":{"modulationColor":0,"modulationControlsExpanded":false}},
{"id":56975,"class":"org.iqe.AudioModulators$Half","parameters":{"running":true},"internal":{"modulationColor":0,"modulationControlsExpanded":false}},
{"id":56976,"class":"org.iqe.AudioModulators$Eighth","parameters":{"running":true},"internal":{"modulationColor":0,"modulationControlsExpanded":false}},
{"id":56977,"class":"org.iqe.AudioModulators$DottedEighth","parameters":{"running":true},"internal":{"modulationColor":0,"modulationControlsExpanded":false}},
{"id":56978,"class":"org.iqe.AudioModulators$Triplet","parameters":{"running":true},"internal":{"modulationColor":0,"modulationControlsExpanded":false}},
{"id":56979,"class":"org.iqe.AudioModulators$VolumeLevel","parameters":{"running":true},"internal":{"modulationColor":0,"modulationControlsExpanded":false}},
{"id":56980,"class":"org.iqe.AudioModulators$BassLevel","parameters":{"running":true},"internal":{"modulationColor":0,"modulationControlsExpanded":false}},
{"id":56981,"class":"org.iqe.AudioModulators$TrebleLevel","parameters":{"running":true},"internal":{"modulationColor":0,"modulationControlsExpanded":false}},
{"id":56982,"class":"org.iqe.AudioModulators$BassRatio","parameters":{"running":true},"internal":{"modulationColor":0,"modulationControlsExpanded":false}},
{"id":56983,"class":"org.iqe.AudioModulators$TrebleRatio","parameters":{"running":true},"internal":{"modulationColor":0,"modulationControlsExpanded":false}},
```

Ordering of events in LX land / engine:
```shell
pbpaste | grep DEBUG | acut -f 2- | freq | sort -nk2
4769 1	DEBUG	New	tick
4769 2	DEBUG	Root	Modulator	tick
4769 3	DEBUG	QuarterClick	tick
4770 4	DEBUG	Global	click	tick
 167 5	DEBUG	Sync	trigger	method
4603 5	DEBUG	Engine	loop	task	tick
 167 6	DEBUG	Engine	loop	task	tick
1002 6	DEBUG	ZipStrip	pattern	run
3600 6	DEBUG	Master	channel	Audio	Effect	run
  36 7	DEBUG	ZipStrip	pattern	run
 131 7	DEBUG	Master	channel	Audio	Effect	run
1002 7	DEBUG	Sync	became	stale
  36 8	DEBUG	Sync	became	stale
1002 8	DEBUG	Master	channel	Audio	Effect	run
  36 9	DEBUG	Master	channel	Audio	Effect	run
  
  
# Again

pbpaste | grep DEBUG | acut -f 2- | freq | sort -nk2
4231 1	DEBUG	New	tick
4231 2	DEBUG	Root	Modulator	tick
4231 3	DEBUG	QuarterClick	tick
4232 4	DEBUG	Global	click	tick
 149 5	DEBUG	Sync	trigger	method
4083 5	DEBUG	Engine	loop	task	tick
 149 6	DEBUG	Engine	loop	task	tick
4083 6	DEBUG	ZipStrip	pattern	run
 149 7	DEBUG	ZipStrip	pattern	run
4083 7	DEBUG	Master	channel	Audio	Effect	run
   1 8	DEBUG	Root	Modulator	tick
 149 8	DEBUG	Master	channel	Audio	Effect	run
   1 9	DEBUG	QuarterClick	tick
   1 10	DEBUG	Global	click	tick
   1 11	DEBUG	Engine	loop	task	tick
   1 12	DEBUG	ZipStrip	pattern	run
   1 13	DEBUG	Master	channel	Audio	Effect	run
   
   
# Sigh last time, forgot pattern modulators, note order
pbpaste | grep DEBUG | acut -f 2- | freq | sort -nk2
1391 1	DEBUG	New	tick
1391 2	DEBUG	Root	Modulator	tick
1391 3	DEBUG	QuarterClick	tick
1391 4	DEBUG	Global	click	tick
  49 5	DEBUG	Sync	trigger	method
1342 5	DEBUG	Engine	loop	task	tick
  49 6	DEBUG	Engine	loop	task	tick
1342 6	DEBUG	Pattern	modulator	tick
  49 7	DEBUG	Pattern	modulator	tick
1342 7	DEBUG	ZipStrip	pattern	run
  49 8	DEBUG	ZipStrip	pattern	run
1342 9	DEBUG	Master	channel	Audio	Effect	run
  49 10	DEBUG	Master	channel	Audio	Effect	run
```