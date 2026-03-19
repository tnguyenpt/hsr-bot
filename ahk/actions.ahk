#Requires AutoHotkey v2.0

if (A_Args.Length < 1) {
    ExitApp 1
}

action := A_Args[1]

try {
    switch action {
        case "click":
            x := Integer(A_Args[2])
            y := Integer(A_Args[3])
            MouseMove x, y, 5
            Sleep 100
            Click

        case "press":
            key := A_Args[2]
            Send "{" key "}"

        case "hotkey":
            combo := A_Args[2]
            ; examples: ^a, !{Tab}, +{F10}
            Send combo

        case "type":
            txt := A_Args[2]
            SendText txt

        case "alt_tap":
            Send "{Alt down}"
            Sleep 150
            Send "{Alt up}"

        default:
            ExitApp 2
    }
    ExitApp 0
} catch as err {
    ExitApp 3
}
