import * as THREE from './three/three.module.js';
import { scene } from './scene.js';
import { updateHotbar } from './hotbar.js';

const powerUps = new Map();

export function createPowerUpSprite(powerUp) {
    const size = 80;
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');
    
    // Effet de lueur
    const gradient = ctx.createRadialGradient(
        size/2, size/2, 0,
        size/2, size/2, size/2
    );
    gradient.addColorStop(0, powerUp.properties.color);
    gradient.addColorStop(0.6, powerUp.properties.color);
    gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
    
    ctx.beginPath();
    ctx.arc(size/2, size/2, size/2, 0, Math.PI * 2);
    ctx.fillStyle = gradient;
    ctx.fill();
    
    // Effet de pulsation
    const sprite = new THREE.Sprite(new THREE.SpriteMaterial({
        map: new THREE.CanvasTexture(canvas),
        transparent: true,
        blending: THREE.AdditiveBlending
    }));
    
    sprite.position.set(powerUp.x, powerUp.y, 0);
    sprite.scale.set(size, size, 1);
    
    // Animation de pulsation
    const animate = () => {
        const scale = 1 + Math.sin(Date.now() * 0.003) * 0.2;
        sprite.scale.set(size * scale, size * scale, 1);
        requestAnimationFrame(animate);
    };
    animate();
    
    return sprite;
}

export function createNewPowerUp(newPowerUp) {
    const powerUpArray = Array.isArray(newPowerUp) ? newPowerUp : [newPowerUp];
    powerUpArray.forEach(powerUp => {
        if (!powerUps.has(powerUp.id)) {
            const sprite = createPowerUpSprite(powerUp);
            scene.add(sprite);
            powerUps.set(powerUp.id, sprite);
        }
    });
}

export function updatePowerUps(newPowerUps) {
    // S'assurer que newPowerUps est un tableau
    const powerUpArray = Array.isArray(newPowerUps) ? newPowerUps : [newPowerUps];

    // Mise à jour des power-ups existants
    powerUps.forEach((sprite, id) => {
        if (!powerUpArray.find(p => p.id === id)) {
            sprite.removeFromParent();
            powerUps.delete(id);
        }
    });
}

export function displayPowerUpCollected(powerUp, isCollected = false) {
    console.log('Displaying power-up effect:', powerUp, 'isCollected:', isCollected);
    
    // Supprimer les anciens effets s'il y en avait
    const oldEffects = document.querySelectorAll('.power-up-effect');
    oldEffects.forEach(effect => effect.remove());

    const effectDiv = document.createElement('div');
    effectDiv.className = 'power-up-effect';

    let effectText;
    let emoji;
    switch (powerUp.type) {
        case 'speed_boost':
            emoji = '🚀';
            effectText = isCollected ? 'Speed boost collected!' : 'Speed boost activated!';
            break;
        case 'slow_zone':
            emoji = '🐢';
            effectText = isCollected ? 'Slow zone collected!' : 'Speed slowed!';
            break;
        case 'shield':
            emoji = '🛡️';
            effectText = isCollected ? 'Shield collected!' : 'Shield activated!';
            break;
        case 'point_multiplier':
            emoji = '✨';
            effectText = isCollected ? 'Point multiplier collected!' : 'Point multiplier activated!';
            break;
        default:
            emoji = '🎮';
            effectText = isCollected ? `${powerUp.type} collected!` : `${powerUp.type} activated!`;
    }
    
    effectDiv.innerHTML = `${emoji} ${effectText}`;
    
    // Appliquer la couleur du texte si disponible
    if (powerUp.properties && powerUp.properties.text_color) {
        effectDiv.style.color = powerUp.properties.text_color;
    }
    
    document.body.appendChild(effectDiv);
    
    // Ajouter une animation de fondu
    effectDiv.style.animation = 'fadeInOut 2s ease-in-out';
    effectDiv.style.opacity = '0';
    requestAnimationFrame(() => {
        effectDiv.style.opacity = '1';
    });
    
    // Supprimer l'élément après l'animation
    setTimeout(() => {
        if (effectDiv && effectDiv.parentNode) {
            effectDiv.style.opacity = '0';
            setTimeout(() => effectDiv.remove(), 300);
        }
    }, 2000);
}

export function getPowerUps() {
    const powerUpArray = [];
    powerUps.forEach((sprite, id) => {
        powerUpArray.push({
            id: id,
            x: sprite.position.x,
            y: sprite.position.y,
            properties: {
                color: sprite.material.color.getStyle()
            }
        });
    });
    return powerUpArray;
}

export function usePowerUp(socket, slotIndex) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        // Mettre à jour l'affichage uniquement pour le slot utilisé
        const slots = document.querySelectorAll('.hotbar-slot');
        const slotToUpdate = slots[slotIndex];
        if (slotToUpdate) {
            // Conserver uniquement la touche (hotkey)
            const hotkey = slotToUpdate.querySelector('.hotkey');
            slotToUpdate.innerHTML = '';
            if (hotkey) {
                slotToUpdate.appendChild(hotkey);
            }
        // Envoyer d'abord la requête au serveur
        socket.send(JSON.stringify({
            type: 'use_power_up',
            slot: slotIndex
        }));
        }
    }
}
