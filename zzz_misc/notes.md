# Notes / Scratchy Scratch Scratch


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