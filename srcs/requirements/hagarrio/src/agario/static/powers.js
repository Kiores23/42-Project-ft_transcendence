import * as THREE from './three/three.module.js';
import { scene } from './scene.js';

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

export function displayPowerUpEffect(powerUp) {
    console.log('Displaying power-up effect:', powerUp);
    // Supprimer les anciens effets s'il y en a
    const oldEffects = document.querySelectorAll('.power-up-effect');
    oldEffects.forEach(effect => effect.remove());

    const effectDiv = document.createElement('div');
    effectDiv.className = 'power-up-effect';
    
    let effectText;
    let emoji;
    switch (powerUp.type) {
        case 'speed_boost':
            emoji = '🚀';
            effectText = 'Speed boost !';
            break;
        case 'slow_zone':
            emoji = '🐌';
            effectText = 'Speed slowed !';
            break;
        case 'shield':
            emoji = '🛡️';
            effectText = 'Shield activated !';
            break;
        case 'point_multiplier':
            emoji = '✨';
            effectText = 'Point multiplier !';
            break;
        default:
            emoji = '🎮';
            effectText = `${powerUp.type} activated !`;
    }
    
    effectDiv.innerHTML = `${emoji} ${effectText}`;
    effectDiv.style.color = powerUp.properties.text_color;
    
    document.body.appendChild(effectDiv);
    
    // Supprimer l'élément après l'animation
    setTimeout(() => {
        if (effectDiv && effectDiv.parentNode) {
            effectDiv.remove();
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
        socket.send(JSON.stringify({
            type: 'use_power_up',
            slot: slotIndex
        }));
    }
}
