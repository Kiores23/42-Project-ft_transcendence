import * as THREE from '../../js/three.module.js';
import { loadTexture } from '../load.js';
import { scene } from '../scene.js';

async function createPlateau(tree, team_size) {
    try {
        const boxWidth = 10 * team_size;
        const boxHeight = 6;
        const horizontalSpacing = 10;
        const verticalSpacing = 10;

        // Calculer la taille du plateau
        let maxWidth = 0;
        for (let level = 0; level < tree.length; level++) {
            const currentLevel = tree[level];
            const levelWidth = currentLevel.length * (boxWidth + horizontalSpacing);
            if (levelWidth > maxWidth) {
                maxWidth = levelWidth;
            }
        }
        const maxHeight = tree.length * verticalSpacing + boxHeight / 2;

        // Charger la texture et créer le plateau
        async function loadRandomPlateauTexture() {
            // Générer un nombre aléatoire entre 1 et 6
            const randomIndex = Math.floor(Math.random() * 8) + 1;
        
            // Construire le chemin du fichier correspondant
            const filePath = `plateau${randomIndex}.jpeg`;
        
            // Charger la texture
            const texture = await loadTexture(filePath);
            return texture;
        }
        const texture = await loadRandomPlateauTexture();
        const plateauGeometry = new THREE.BoxGeometry(maxWidth, maxHeight, 2);
        const plateauMaterial = new THREE.MeshStandardMaterial({
            map: texture,
        });
        const plateau = new THREE.Mesh(plateauGeometry, plateauMaterial);
        plateau.position.set(-boxWidth / 2, -maxHeight / 2 + boxHeight, -1.5);
        scene.add(plateau);

        // Ajouter une lumière directionnelle
        const light = new THREE.DirectionalLight(0xffffff, 3);
        light.position.set(10, 10, 10);
        light.castShadow = true; // Activer les ombres projetées
        light.shadow.mapSize.width = 1024; // Taille de la carte d'ombres
        light.shadow.mapSize.height = 1024;
        scene.add(light);

        // Ajouter une lumière ambiante
        const ambientLight = new THREE.AmbientLight(0x404040, 1);
        scene.add(ambientLight);

    } catch (error) {
        console.error('Error:', error);
    }
}


export { createPlateau };
