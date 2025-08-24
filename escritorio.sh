#!/bin/bash

echo "Elige tu gestor de ventanas:"
echo "1. I3wm"
echo "2. Openbox"
echo "3. Icewm"
echo "4. Fluxbox"
echo "5. Jwm"
echo "6. Pekwm"
echo "7. Evilwm"
read opcion

case $opcion in
    1)
        gestor="i3"
        ;;
    2)
        gestor="openbox-session"
        ;;
    3)
	gestor="icewm-session"
	;;
    4)
	gestor="startfluxbox"
	;;
    5)
	gestor="jwm"
	;;
	6)
	gestor="pekwm"
	;;
	7)
	gestor="evilwm"
	;;
    *)
        echo "Opción inválida"
        exit 1
        ;;
esac

startx /usr/bin/$gestor


