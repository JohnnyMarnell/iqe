// adapted from https://github.com/madsstoumann
class XYPad extends EventTarget {
    constructor(pad) {
        super()
        this.pad = pad
        this.x = 0
        this.y = 0
        this.init(pad)
    }

    init(pad) {
        let active = false;
        let btn = pad.querySelector('*');
        // const edge = btn.offsetWidth / 2;
        const edge = 0;
        const rect = pad.getBoundingClientRect();
    
        let xCurrent = 0;
        let yCurrent = 0;
        let xInitial;
        let yInitial;
        const xMax = rect.width - btn.offsetWidth;
        const yMax = rect.height - btn.offsetHeight;
        let xOffset = 0;
        let yOffset = 0;
    
        // pad.addEventListener('keydown', key);
        pad.addEventListener("pointerdown", down, false);
        pad.addEventListener("pointerup", up, false);
        pad.addEventListener("pointermove", move, false);
    
        // pad.addEventListener("touchstart", down, false);
        // pad.addEventListener("touchend", up, false);
        const moveUpdate = (e) => {
            if (!active) return
            let x = (xOffset + btn.offsetWidth / 2) / rect.width
            let y = 1 - (yOffset + btn.offsetHeight / 2) / rect.height
            x = Math.min(1.0, Math.max(0.0, x))
            y = Math.min(1.0, Math.max(0.0, y))
            this.x = x
            this.y = y
            this.pad.dispatchEvent(new CustomEvent("xy", { detail: {x,y} }))
        }
        pad.addEventListener("touchmove", moveUpdate);
        pad.addEventListener("pointermove", moveUpdate);
    
        function down(e) {
            xInitial = e.clientX - xOffset;
            yInitial = e.clientY - yOffset;
            if (e.target === btn) active = true;
        }
    
        function up(e) {
            xInitial = xCurrent;
            yInitial = yCurrent;
            active = false;
        }
    
        function move(e) {
            if (active) {
                e.preventDefault();
                xCurrent = e.clientX - xInitial;
                yCurrent = e.clientY - yInitial;
                update(xCurrent, yCurrent);
            }
        }
    
        function update(x, y) {
            xOffset = x;
            yOffset = y;
            const xMove = x >= 0 - edge && x <= xMax;
            const yMove = y >= 0 - edge && y <= yMax;
            btn.style.transform = `translate3d(${x}px, ${y}px, 0)`;
        }
    }
}

export default XYPad