// Funciones JavaScript para ERP Educativo

// Confirmar acciones críticas
function confirmarAccion(mensaje) {
    return confirm(mensaje);
}

// Actualizar datos en tiempo real (polling simple)
function actualizarDatos(url, intervalo = 5000) {
    setInterval(() => {
        fetch(url)
            .then(response => response.json())
            .then(data => {
                console.log('Datos actualizados:', data);
                // Actualizar la UI con los nuevos datos
            })
            .catch(error => console.error('Error:', error));
    }, intervalo);
}

// Validar formularios
function validarFormulario(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required]');
    
    inputs.forEach(input => {
        if (!input.value) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Formatear números como moneda
function formatearMoneda(valor) {
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP'
    }).format(valor);
}

// Mostrar notificación toast
function mostrarNotificacion(mensaje, tipo = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${tipo} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        ${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Crear gráfico con Chart.js
function crearGrafico(canvasId, tipo, etiquetas, datos, titulo) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    new Chart(ctx, {
        type: tipo,
        data: {
            labels: etiquetas,
            datasets: [{
                label: titulo,
                data: datos,
                backgroundColor: [
                    'rgba(102, 126, 234, 0.5)',
                    'rgba(118, 75, 162, 0.5)',
                    'rgba(86, 171, 47, 0.5)',
                    'rgba(242, 153, 74, 0.5)',
                    'rgba(33, 147, 176, 0.5)'
                ],
                borderColor: [
                    'rgba(102, 126, 234, 1)',
                    'rgba(118, 75, 162, 1)',
                    'rgba(86, 171, 47, 1)',
                    'rgba(242, 153, 74, 1)',
                    'rgba(33, 147, 176, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Calcular métricas de inventario
function calcularMetricasInventario(cantidadActual, puntoReorden, stockSeguridad) {
    const estado = {
        nivel: 'normal',
        mensaje: '',
        color: 'success'
    };
    
    if (cantidadActual <= stockSeguridad) {
        estado.nivel = 'critico';
        estado.mensaje = '¡Stock crítico! Ordenar inmediatamente';
        estado.color = 'danger';
    } else if (cantidadActual <= puntoReorden) {
        estado.nivel = 'bajo';
        estado.mensaje = 'Stock bajo. Considerar orden de compra';
        estado.color = 'warning';
    } else {
        estado.mensaje = 'Nivel de stock adecuado';
    }
    
    return estado;
}

// Exportar datos a CSV
function exportarCSV(datos, nombreArchivo) {
    const csvContent = datos.map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = nombreArchivo;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Event listeners al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts después de 5 segundos
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 150);
        }, 5000);
    });
    
    // Confirmar acciones de eliminación
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('¿Está seguro de que desea eliminar este elemento?')) {
                e.preventDefault();
            }
        });
    });
});
